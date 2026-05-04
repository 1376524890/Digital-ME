import json
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from src.db.models import ProfileSnapshot as ProfileSnapshotModel
from src.db.models import Ply, Session, StructuredObject
from src.db.session import AsyncSessionLocal, get_db
from src.llm.factory import get_llm
from src.memory_hub.distiller import get_distiller
from src.memory_hub.indexer import get_indexer
from src.psyche_probe.gap_scorer import TARGETS, compute_gaps
from src.psyche_probe.ocean_estimator import get_ocean_estimator
from src.psyche_probe.response_generator import get_generator
from src.psyche_probe.state_builder import get_state_builder
from src.psyche_probe.strategy_planner import get_planner

router = APIRouter(prefix="/interview", tags=["interview"])


class StartRequest(BaseModel):
    user_id: str
    context: str | None = None


class StartResponse(BaseModel):
    session_id: str
    greeting: str


class SendMessageRequest(BaseModel):
    text: str


class SessionMutationResponse(BaseModel):
    session_id: str
    status: str


class EndInterviewResponse(SessionMutationResponse):
    skill_file_id: str
    token_count: int
    warnings: list[str]


WELCOME_SYSTEM = """你是一位温暖、富有同理心的 AI 采访者。你的目标是深入了解用户——
他们的个性、思维模式、沟通风格、价值观和偏好。

沟通准则：
- 对话自然，避免使用临床术语
- 每次回复末尾提出一个开放式问题
- 回复简洁（2-4 句话）
- 匹配用户的语气和用词习惯
- 始终使用简体中文回复，禁止使用英文。
"""


async def _distill_and_index(session_id: uuid.UUID, ply_id: uuid.UUID, user_text: str, ai_response: str):
    """Background task: distill Ply → StructuredObject + generate embedding."""
    try:
        async with AsyncSessionLocal() as db:
            distiller = get_distiller()
            distilled = await distiller.distill(user_text, ai_response)

            obj = StructuredObject(
                ply_id=ply_id,
                session_id=session_id,
                exchange_core=distilled["exchange_core"],
                specific_context=distilled["specific_context"],
                room_assignments=distilled["room_assignments"],
                files_touched=distilled["files_touched"],
                confidence=0.85,
            )
            db.add(obj)
            await db.commit()

            # Generate embedding (can be slow due to model)
            try:
                indexer = get_indexer()
                await indexer.index_object(db, obj)
            except Exception as e:
                print(f"Embedding generation failed for ply {ply_id}: {e}")
    except Exception as e:
        print(f"Distillation failed for ply {ply_id}: {e}")


def _profile_payload(profile: ProfileSnapshotModel) -> dict:
    return {
        "pppppi_slots": profile.pppppi_slots or {},
        "bdi_model": profile.bdi_model or {},
        "ocean_scores": profile.ocean_scores or {},
        "cognitive_errors": profile.cognitive_errors or [],
        "vocabulary_profile": profile.vocabulary_profile or {},
        "syntax_preferences": profile.syntax_preferences or [],
        "key_taboos": profile.key_taboos or [],
    }


def _merge_cognitive_errors(existing: list[dict], new: list[dict]) -> list[dict]:
    merged = list(existing or [])
    seen_contexts = {
        item.get("context")
        for item in merged
        if isinstance(item, dict) and item.get("context")
    }
    for item in new or []:
        if not isinstance(item, dict):
            continue
        context = item.get("context")
        if not context or context in seen_contexts:
            continue
        seen_contexts.add(context)
        merged.append(item)
    return merged


def _apply_profile_payload(profile: ProfileSnapshotModel, payload: dict) -> None:
    profile.pppppi_slots = payload["pppppi_slots"]
    profile.bdi_model = payload["bdi_model"]
    profile.ocean_scores = payload["ocean_scores"]
    profile.cognitive_errors = payload["cognitive_errors"]
    profile.vocabulary_profile = payload["vocabulary_profile"]
    profile.syntax_preferences = payload["syntax_preferences"]
    profile.key_taboos = payload["key_taboos"]
    profile.updated_at = datetime.now(timezone.utc)


def _build_coverage(pppppi_slots: dict) -> dict[str, float]:
    coverage = {}
    for dim, target in TARGETS.items():
        slot = pppppi_slots.get(dim, {})
        evidence_count = len(slot.get("evidence", []))
        coverage[dim] = round(min(evidence_count / target, 1.0), 2)
    coverage["overall"] = round(sum(coverage.values()) / len(TARGETS), 2) if coverage else 0.0
    return coverage


def _build_recent_context(recent_plys: list[Ply], user_text: str) -> str:
    messages = []
    for ply in recent_plys:
        messages.append({"role": "user", "content": ply.user_text})
        messages.append({"role": "assistant", "content": ply.ai_response})
    messages.append({"role": "user", "content": user_text})
    return " ".join(
        f"User: {message['content']}"
        for message in messages[-3:]
        if message["role"] == "user"
    )


async def _prepare_turn(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_text: str,
) -> dict:
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session is not active")

    result = await db.execute(
        select(Ply)
        .where(Ply.session_id == session_id)
        .order_by(Ply.sequence_num.desc())
        .limit(10)
    )
    recent_plys = list(result.scalars().all())
    recent_plys.reverse()

    profile = await _ensure_profile(db, session_id)
    current_profile = _profile_payload(profile)

    builder = get_state_builder()
    psy_update = await builder.build(user_text, current_profile)
    updated_profile = {
        **current_profile,
        "pppppi_slots": psy_update["pppppi_slots"],
        "bdi_model": psy_update["bdi_model"],
        "cognitive_errors": _merge_cognitive_errors(
            current_profile["cognitive_errors"],
            psy_update["cognitive_errors"],
        ),
        "vocabulary_profile": psy_update["vocabulary_profile"],
        "syntax_preferences": psy_update["syntax_preferences"],
        "key_taboos": psy_update["key_taboos"],
    }

    ocean_estimator = get_ocean_estimator()
    updated_profile["ocean_scores"] = await ocean_estimator.estimate(updated_profile)

    _apply_profile_payload(profile, updated_profile)
    await db.commit()

    recent_ctx = _build_recent_context(recent_plys, user_text)
    planner = get_planner()
    plan = await planner.plan(updated_profile, recent_ctx)

    return {
        "session": session,
        "profile": updated_profile,
        "plan": plan,
        "coverage": _build_coverage(updated_profile["pppppi_slots"]),
        "gaps": compute_gaps(updated_profile["pppppi_slots"]),
        "recent_context": recent_ctx,
        "next_sequence_num": (recent_plys[-1].sequence_num + 1) if recent_plys else 1,
    }


async def _persist_ply(
    db: AsyncSession,
    session_id: uuid.UUID,
    sequence_num: int,
    user_text: str,
    ai_response: str,
) -> Ply:
    ply = Ply(
        session_id=session_id,
        sequence_num=sequence_num,
        user_text=user_text,
        ai_response=ai_response,
    )
    db.add(ply)
    await db.commit()
    return ply


def _queue_distillation(
    session_id: uuid.UUID,
    ply_id: uuid.UUID,
    user_text: str,
    ai_response: str,
) -> None:
    import asyncio

    asyncio.create_task(_distill_and_index(session_id, ply_id, user_text, ai_response))


async def _ensure_profile(db: AsyncSession, session_id: uuid.UUID) -> ProfileSnapshotModel:
    result = await db.execute(
        select(ProfileSnapshotModel).where(ProfileSnapshotModel.session_id == session_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = ProfileSnapshotModel(session_id=session_id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


@router.get("/{session_id}/state")
async def get_session_state(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get session state including whether AI should initiate conversation."""
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check if session has any messages
    result = await db.execute(
        select(Ply)
        .where(Ply.session_id == session_id)
        .order_by(Ply.sequence_num.asc())
    )
    plys = list(result.scalars().all())

    # If no messages yet, generate a fresh greeting
    greeting = None
    messages = []
    if not plys:
        greeting = (session.metadata_ or {}).get("greeting")
        if not greeting:
            llm = get_llm()
            greeting = await llm.generate(
                system_prompt=WELCOME_SYSTEM,
                messages=[
                    {
                        "role": "user",
                        "content": "发起对话。做个简短的自我介绍，然后提一个开放式问题来了解我。",
                    }
                ],
                temperature=0.8,
                max_tokens=200,
            )
            session.metadata_ = {**(session.metadata_ or {}), "greeting": greeting}
            await db.commit()
    else:
        # Return all messages so frontend can restore chat history
        for p in plys:
            messages.append({
                "id": str(p.id),
                "role": "user",
                "content": p.user_text,
                "sequence_num": p.sequence_num,
            })
            messages.append({
                "id": str(p.id) + "_ai",
                "role": "assistant",
                "content": p.ai_response,
                "sequence_num": p.sequence_num,
            })

    # Get coverage from profile snapshot
    profile = await _ensure_profile(db, session_id)
    coverage = _build_coverage(profile.pppppi_slots or {})

    return {
        "session_id": str(session.id),
        "status": session.status,
        "message_count": len(plys),
        "greeting": greeting,
        "messages": messages,
        "coverage": coverage,
    }


@router.post("/start", response_model=StartResponse)
async def start_interview(body: StartRequest, db: AsyncSession = Depends(get_db)):
    session = Session(user_id=body.user_id, status="active", metadata_={})
    if body.context:
        session.metadata_["initial_context"] = body.context
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # Ensure profile snapshot exists
    await _ensure_profile(db, session.id)

    llm = get_llm()
    context_note = f' The user said: "{body.context}".' if body.context else ""
    greeting = await llm.generate(
        system_prompt=WELCOME_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": f"Start a conversation. Introduce yourself briefly and ask an opening question.{context_note}",
            }
        ],
        temperature=0.8,
        max_tokens=256,
    )
    session.metadata_ = {**(session.metadata_ or {}), "greeting": greeting}
    await db.commit()

    return StartResponse(session_id=str(session.id), greeting=greeting)


@router.post("/{session_id}/message")
async def send_message(
    session_id: uuid.UUID,
    body: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    prepared = await _prepare_turn(db, session_id, body.text)
    generator = get_generator()
    response_text = await generator.generate(
        prepared["plan"],
        prepared["profile"],
        prepared["recent_context"],
    )
    ply = await _persist_ply(
        db,
        session_id,
        prepared["next_sequence_num"],
        body.text,
        response_text,
    )

    # ── Memory Distillation (async, non-blocking to response) ──
    result = {
        "ply_id": str(ply.id),
        "response": response_text,
        "sequence_num": prepared["next_sequence_num"],
        "gaps": prepared["gaps"],
        "strategy": prepared["plan"].get("strategy"),
        "target_dimension": prepared["plan"].get("target_dimension"),
        "coverage": prepared["coverage"],
    }
    _queue_distillation(session_id, ply.id, body.text, response_text)

    return result


@router.post("/{session_id}/message/stream")
async def send_message_stream(
    session_id: uuid.UUID,
    body: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    prepared = await _prepare_turn(db, session_id, body.text)
    generator = get_generator()

    async def event_stream() -> AsyncIterator[str]:
        full_response = ""
        async for token in generator.generate_stream(
            prepared["plan"],
            prepared["profile"],
            prepared["recent_context"],
        ):
            full_response += token
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        async with AsyncSessionLocal() as write_db:
            ply = await _persist_ply(
                write_db,
                session_id,
                prepared["next_sequence_num"],
                body.text,
                full_response,
            )
            _queue_distillation(session_id, ply.id, body.text, full_response)
            yield f"data: {json.dumps({'type': 'done', 'ply_id': str(ply.id), 'sequence_num': prepared['next_sequence_num'], 'gaps': prepared['gaps'], 'strategy': prepared['plan'].get('strategy'), 'target_dimension': prepared['plan'].get('target_dimension'), 'coverage': prepared['coverage']})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{session_id}/abandon", response_model=SessionMutationResponse)
async def abandon_interview(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "active":
        raise HTTPException(status_code=400, detail="Only active sessions can be abandoned")

    await db.execute(delete(StructuredObject).where(StructuredObject.session_id == session_id))
    await db.execute(delete(Ply).where(Ply.session_id == session_id))
    await db.execute(delete(ProfileSnapshotModel).where(ProfileSnapshotModel.session_id == session_id))
    from src.db.models import SkillFile

    await db.execute(delete(SkillFile).where(SkillFile.session_id == session_id))
    await db.execute(delete(Session).where(Session.id == session_id))
    await db.commit()

    return SessionMutationResponse(session_id=str(session_id), status="abandoned")


@router.post("/{session_id}/end", response_model=EndInterviewResponse)
async def end_interview(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)
    await db.commit()

    # Generate SKILL.md
    profile = await _ensure_profile(db, session_id)
    from src.skill_generator.builder import get_builder

    builder = get_builder()
    skill_result = await builder.build(
        db,
        str(session_id),
        {
            "pppppi_slots": profile.pppppi_slots or {},
            "bdi_model": profile.bdi_model or {},
            "ocean_scores": profile.ocean_scores or {},
            "cognitive_errors": profile.cognitive_errors or [],
            "vocabulary_profile": profile.vocabulary_profile or {},
            "syntax_preferences": profile.syntax_preferences or [],
            "key_taboos": profile.key_taboos or [],
        },
    )

    return {
        "session_id": str(session_id),
        "status": "completed",
        "skill_file_id": skill_result["skill_file_id"],
        "token_count": skill_result["token_count"],
        "warnings": skill_result["warnings"],
    }
