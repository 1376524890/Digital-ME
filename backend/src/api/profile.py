import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import ProfileSnapshot
from src.db.session import get_db

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/{session_id}")
async def get_profile(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    result = await db.execute(
        select(ProfileSnapshot).where(ProfileSnapshot.session_id == session_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {
        "session_id": str(profile.session_id),
        "pppppi_slots": profile.pppppi_slots,
        "bdi_model": profile.bdi_model,
        "ocean_scores": profile.ocean_scores,
        "cognitive_errors": profile.cognitive_errors,
        "vocabulary_profile": profile.vocabulary_profile,
        "syntax_preferences": profile.syntax_preferences,
        "key_taboos": profile.key_taboos,
    }


@router.get("/{session_id}/coverage")
async def get_coverage(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    result = await db.execute(
        select(ProfileSnapshot).where(ProfileSnapshot.session_id == session_id)
    )
    profile = result.scalar_one_or_none()

    default_coverage = {
        "presenting": 0.0,
        "predisposing": 0.0,
        "precipitating": 0.0,
        "perpetuating": 0.0,
        "protective": 0.0,
        "impact": 0.0,
    }

    if not profile:
        return default_coverage

    targets = {
        "presenting": 5,
        "predisposing": 4,
        "precipitating": 3,
        "perpetuating": 4,
        "protective": 3,
        "impact": 3,
    }

    coverage = {}
    for dim, target in targets.items():
        slot = profile.pppppi_slots.get(dim, {})
        evidence_count = len(slot.get("evidence", []))
        confidence = slot.get("confidence", 0.0)
        coverage[dim] = min(evidence_count / target * confidence, 1.0)

    return coverage
