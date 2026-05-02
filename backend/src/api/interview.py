import json
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from src.db.models import ProfileSnapshot as ProfileSnapshotModel
from src.db.models import Ply, Session, StructuredObject
from src.db.session import AsyncSessionLocal, get_db
from src.llm.factory import get_llm
from src.memory_hub.distiller import get_distiller
from src.memory_hub.indexer import get_indexer
from src.psyche_probe.gap_scorer import compute_gaps
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


WELCOME_SYSTEM = """你是一位温暖、富有同理心的 AI 采访者。你的目标是深入了解用户——
他们的个性、思维模式、沟通风格、价值观和偏好。

沟通准则：
- 对话自然，避免使用临床术语
- 每次回复末尾提出一个开放式问题
- 回复简洁（2-4 句话）
- 匹配用户的语气和用词习惯
- 使用简体中文回复
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

    return {
        "session_id": str(session.id),
        "status": session.status,
        "message_count": len(plys),
        "greeting": greeting,
        "messages": messages,
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

    return StartResponse(session_id=str(session.id), greeting=greeting)


@router.post("/{session_id}/message")
async def send_message(
    session_id: uuid.UUID,
    body: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(Session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session is not active")

    # Get conversation history
    result = await db.execute(
        select(Ply)
        .where(Ply.session_id == session_id)
        .order_by(Ply.sequence_num.desc())
        .limit(10)
    )
    recent_plys = list(result.scalars().all())
    recent_plys.reverse()

    # Build message context
    messages = []
    for p in recent_plys:
        messages.append({"role": "user", "content": p.user_text})
        messages.append({"role": "assistant", "content": p.ai_response})
    messages.append({"role": "user", "content": body.text})

    # ── PsyProbe: Extract psychological markers ──
    profile = await _ensure_profile(db, session_id)
    current_profile = {
        "pppppi_slots": profile.pppppi_slots or {},
        "bdi_model": profile.bdi_model or {},
        "ocean_scores": profile.ocean_scores or {},
        "cognitive_errors": profile.cognitive_errors or [],
        "vocabulary_profile": profile.vocabulary_profile or {},
    }

    builder = get_state_builder()
    psy_update = await builder.build(body.text, current_profile)

    # Update profile snapshot
    profile.pppppi_slots = psy_update.get("pppppi_slots", current_profile["pppppi_slots"])
    profile.bdi_model = psy_update.get("bdi_model", current_profile["bdi_model"])
    existing_errors = list(profile.cognitive_errors or [])
    new_errors = psy_update.get("cognitive_errors", [])
    for e in new_errors:
        if not any(ex.get("context") == e.get("context") for ex in existing_errors):
            existing_errors.append(e)
    profile.cognitive_errors = existing_errors
    profile.updated_at = datetime.now(timezone.utc)
    await db.commit()

    # ── Strategy Planning ──
    gaps = compute_gaps(profile.pppppi_slots or {})
    recent_ctx = " ".join([f"User: {m['content']}" for m in messages[-3:] if m["role"] == "user"])

    planner = get_planner()
    plan = await planner.plan(
        {**current_profile, "pppppi_slots": profile.pppppi_slots, "bdi_model": profile.bdi_model},
        recent_ctx,
    )

    # ── Response Generation ──
    generator = get_generator()
    response_text = await generator.generate(
        plan,
        {**current_profile, "pppppi_slots": profile.pppppi_slots, "bdi_model": profile.bdi_model, "cognitive_errors": profile.cognitive_errors},
        recent_ctx,
    )

    # Store ply
    next_seq = (recent_plys[-1].sequence_num + 1) if recent_plys else 1
    ply = Ply(
        session_id=session_id,
        sequence_num=next_seq,
        user_text=body.text,
        ai_response=response_text,
    )
    db.add(ply)
    await db.commit()

    # ── Memory Distillation (async, non-blocking to response) ──
    result = {
        "ply_id": str(ply.id),
        "response": response_text,
        "sequence_num": next_seq,
        "gaps": gaps,
        "strategy": plan.get("strategy"),
        "target_dimension": plan.get("target_dimension"),
    }

    # Fire-and-forget distillation
    import asyncio
    asyncio.create_task(_distill_and_index(session_id, ply.id, body.text, response_text))

    return result


@router.post("/{session_id}/message/stream")
async def send_message_stream(
    session_id: uuid.UUID,
    body: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
):
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

    messages = []
    for p in recent_plys:
        messages.append({"role": "user", "content": p.user_text})
        messages.append({"role": "assistant", "content": p.ai_response})
    messages.append({"role": "user", "content": body.text})

    next_seq = (recent_plys[-1].sequence_num + 1) if recent_plys else 1

    # PsyProbe extraction
    profile = await _ensure_profile(db, session_id)
    current_profile = {
        "pppppi_slots": profile.pppppi_slots or {},
        "bdi_model": profile.bdi_model or {},
        "ocean_scores": profile.ocean_scores or {},
        "cognitive_errors": profile.cognitive_errors or [],
        "vocabulary_profile": profile.vocabulary_profile or {},
    }

    builder = get_state_builder()
    psy_update = await builder.build(body.text, current_profile)

    profile.pppppi_slots = psy_update.get("pppppi_slots", current_profile["pppppi_slots"])
    profile.bdi_model = psy_update.get("bdi_model", current_profile["bdi_model"])
    existing_errors = list(profile.cognitive_errors or [])
    new_errors = psy_update.get("cognitive_errors", [])
    for e in new_errors:
        if not any(ex.get("context") == e.get("context") for ex in existing_errors):
            existing_errors.append(e)
    profile.cognitive_errors = existing_errors
    profile.updated_at = datetime.now(timezone.utc)
    await db.commit()

    gaps = compute_gaps(profile.pppppi_slots or {})
    recent_ctx = " ".join([f"User: {m['content']}" for m in messages[-3:] if m["role"] == "user"])

    planner = get_planner()
    plan = await planner.plan(
        {**current_profile, "pppppi_slots": profile.pppppi_slots, "bdi_model": profile.bdi_model},
        recent_ctx,
    )

    generator = get_generator()
    merged_profile = {
        **current_profile,
        "pppppi_slots": profile.pppppi_slots,
        "bdi_model": profile.bdi_model,
        "cognitive_errors": profile.cognitive_errors,
    }

    async def event_stream() -> AsyncIterator[str]:
        full_response = ""
        async for token in generator.generate_stream(plan, merged_profile, recent_ctx):
            full_response += token
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        async with AsyncSessionLocal() as write_db:
            ply = Ply(
                session_id=session_id,
                sequence_num=next_seq,
                user_text=body.text,
                ai_response=full_response,
            )
            write_db.add(ply)
            await write_db.commit()
            yield f"data: {json.dumps({'type': 'done', 'ply_id': str(ply.id), 'sequence_num': next_seq, 'gaps': gaps, 'strategy': plan.get('strategy'), 'target_dimension': plan.get('target_dimension')})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{session_id}/end")
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
