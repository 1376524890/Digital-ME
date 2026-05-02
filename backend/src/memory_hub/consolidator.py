"""Consolidator: Post-session memory merge, dedup, conflict resolution, pruning."""

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import ProfileSnapshot, StructuredObject


class Consolidator:
    def __init__(self):
        pass

    async def consolidate_session(
        self, db: AsyncSession, session_id: str
    ) -> dict:
        """Merge all structured objects, dedup, resolve conflicts, prune."""
        result = await db.execute(
            select(StructuredObject)
            .where(StructuredObject.session_id == session_id)
            .order_by(StructuredObject.created_at)
        )
        objects = list(result.scalars().all())

        if not objects:
            return {"objects": [], "pruned": [], "conflicts": [], "summary": ""}

        # 1. Deduplicate by exchange_core similarity (cosine > 0.92 on embedding)
        kept, pruned = self._dedup_by_embedding(objects)

        # 2. Resolve conflicts (keep most recent)
        resolved = self._resolve_conflicts(kept)

        # 3. Prune low-confidence items
        confident = [obj for obj in resolved if obj.confidence >= 0.3]

        # 4. Generate summary
        summary = self._generate_summary(confident)

        return {
            "objects": confident,
            "pruned": [obj.id for obj in pruned],
            "conflicts": [],  # TODO: implement BDI conflict detection
            "summary": summary,
        }

    def _dedup_by_embedding(
        self, objects: list[StructuredObject]
    ) -> tuple[list[StructuredObject], list[StructuredObject]]:
        """Remove near-duplicate objects based on embedding cosine similarity."""
        def has_embedding(obj):
            return obj.embedding is not None and len(obj.embedding) > 0

        objects_with_emb = [obj for obj in objects if has_embedding(obj)]
        objects_without_emb = [obj for obj in objects if not has_embedding(obj)]

        kept = []
        pruned = []

        for obj in objects_with_emb:
            is_dup = False
            for kept_obj in kept:
                if has_embedding(kept_obj):
                    try:
                        similarity = self._cosine_similarity(obj.embedding, kept_obj.embedding)
                        if similarity > 0.92:
                            if obj.confidence > kept_obj.confidence:
                                kept.remove(kept_obj)
                                pruned.append(kept_obj)
                            else:
                                pruned.append(obj)
                                is_dup = True
                                break
                    except Exception:
                        continue  # Skip problematic comparisons
            if not is_dup:
                kept.append(obj)

        return kept + objects_without_emb, pruned

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        a_arr = np.asarray(a, dtype=float).flatten()
        b_arr = np.asarray(b, dtype=float).flatten()
        norm_a = np.linalg.norm(a_arr)
        norm_b = np.linalg.norm(b_arr)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a_arr, b_arr) / (norm_a * norm_b))

    def _resolve_conflicts(
        self, objects: list[StructuredObject]
    ) -> list[StructuredObject]:
        """Resolve conflicts: when two objects have contradictory info, keep most recent."""
        # Simple implementation: sort by created_at descending, then dedup exchange_core
        seen_cores = set()
        resolved = []
        for obj in sorted(objects, key=lambda o: o.created_at or "", reverse=True):
            core_lower = obj.exchange_core.lower()
            if core_lower not in seen_cores:
                seen_cores.add(core_lower)
                resolved.append(obj)
        return resolved

    def _generate_summary(self, objects: list[StructuredObject]) -> str:
        """Generate a high-level summary from consolidated objects."""
        all_cores = [obj.exchange_core for obj in objects[:5]]
        return "; ".join(all_cores) if all_cores else ""


_consolidator: Consolidator | None = None


def get_consolidator() -> Consolidator:
    global _consolidator
    if _consolidator is None:
        _consolidator = Consolidator()
    return _consolidator
