import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import SkillFile
from src.db.session import get_db

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/{session_id}/skill.md", response_class=PlainTextResponse)
async def export_skill(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SkillFile).where(SkillFile.session_id == session_id)
    )
    skill_file = result.scalar_one_or_none()
    if not skill_file:
        raise HTTPException(status_code=404, detail="SKILL.md not yet generated")

    return PlainTextResponse(
        content=skill_file.full_content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename=SKILL_{session_id}.md"
        },
    )
