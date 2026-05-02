"""SKILL.md Builder: orchestrates full SKILL.md generation."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import SkillFile, StructuredObject
from src.memory_hub.consolidator import get_consolidator
from src.skill_generator.md_composer import MDComposer
from src.skill_generator.validator import Validator
from src.skill_generator.yaml_composer import YAMLComposer


class SkillBuilder:
    def __init__(self):
        self.yaml_composer = YAMLComposer()
        self.md_composer = MDComposer()
        self.validator = Validator()
        self.consolidator = get_consolidator()

    async def build(
        self, db: AsyncSession, session_id: str, profile: dict
    ) -> dict:
        """Generate a complete SKILL.md from profile and structured objects."""
        # 1. Consolidate structured objects
        try:
            consolidated = await self.consolidator.consolidate_session(db, session_id)
            objects = consolidated.get("objects", [])
        except Exception as e:
            print(f"Consolidation failed: {e}")
            objects = []

        # 2. Estimate OCEAN scores
        try:
            ocean = await self.yaml_composer.estimate_ocean(profile)
        except Exception as e:
            print(f"OCEAN estimation failed: {e}")
            ocean = {"o": 0.5, "c": 0.5, "e": 0.5, "a": 0.5, "n": 0.5}

        # 3. Compose YAML frontmatter
        yaml_fm = self.yaml_composer.compose(profile, ocean)

        # 4. Compose global notes
        obj_dicts = []
        for obj in objects:
            if hasattr(obj, "__dict__"):
                obj_dicts.append(
                    {
                        "exchange_core": obj.exchange_core,
                        "specific_context": obj.specific_context,
                        "room_assignments": obj.room_assignments,
                        "created_at": obj.created_at,
                    }
                )
        global_notes = self.md_composer.compose(obj_dicts, profile)

        # 5. Assemble full SKILL.md
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        full_content = f"""---
# Digital Me Profile
# Generated: {generated_at}
# Version: 1.0

{yaml_fm}
---

# Precedence Rules
1. User's current latest instruction has HIGHEST priority (absolute obedience)
2. Structured core Profile above is the personality baseline (do not contradict)
3. Global Memory Notes below are advisory — if conflicting with current request, ask for clarification

---

{global_notes}

## Thought Trace Protocol
Before each response, internally reason:
1. Check BDI: What beliefs/desires/intentions are relevant?
2. Retrieve specific_context from memory that applies
3. Apply vocabulary and syntax preferences
4. Generate response matching this user's style
"""

        # 6. Validate
        validation = self.validator.validate(yaml_fm, global_notes, full_content)

        # 7. Store SkillFile
        skill_file = SkillFile(
            session_id=session_id,
            version=1,
            yaml_frontmatter=yaml_fm,
            global_notes=global_notes,
            full_content=full_content,
        )
        db.add(skill_file)
        await db.commit()
        await db.refresh(skill_file)

        return {
            "skill_file_id": str(skill_file.id),
            "session_id": session_id,
            "full_content": full_content,
            "token_count": validation["token_count"],
            "yaml_valid": validation["valid"],
            "warnings": validation["warnings"],
        }


_builder: SkillBuilder | None = None


def get_builder() -> SkillBuilder:
    global _builder
    if _builder is None:
        _builder = SkillBuilder()
    return _builder
