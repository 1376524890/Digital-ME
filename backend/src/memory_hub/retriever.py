"""Retriever: Cross-layer fusion (BM25 + HNSW) with RRF."""

import numpy as np
from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import StructuredObject
from src.memory_hub.indexer import get_indexer

RRF_K = 60


class Retriever:
    def __init__(self):
        self.indexer = get_indexer()

    async def hybrid_search(
        self,
        db: AsyncSession,
        query: str,
        session_id: str,
        top_k: int = 20,
        alpha: float = 0.5,
    ) -> list[dict]:
        """RRF fusion of BM25 (verbatim) + HNSW (distilled)."""
        # Get all structured objects for this session
        result = await db.execute(
            select(StructuredObject)
            .where(StructuredObject.session_id == session_id)
            .order_by(StructuredObject.created_at.desc())
            .limit(100)
        )
        all_objects = list(result.scalars().all())

        if not all_objects:
            return []

        # ── BM25 search (keyword) ──
        corpus = [f"{obj.exchange_core} {obj.specific_context}".lower().split() for obj in all_objects]
        bm25 = BM25Okapi(corpus)
        tokenized_query = query.lower().split()
        bm25_scores = bm25.get_scores(tokenized_query) if tokenized_query else np.zeros(len(all_objects))

        # Normalize BM25 scores to [0, 1]
        max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1
        bm25_normalized = bm25_scores / max_bm25

        # ── Vector search (HNSW) ──
        vector_results = await self.indexer.vector_search(db, query, session_id, top_k)
        vector_score_map = {str(obj.id): sim for obj, sim in vector_results}

        # ── RRF fusion ──
        # Rank by BM25
        bm25_ranked = sorted(
            enumerate(bm25_normalized), key=lambda x: -x[1]
        )
        bm25_ranks = {}
        for rank, (idx, _) in enumerate(bm25_ranked):
            bm25_ranks[str(all_objects[idx].id)] = rank + 1

        # Rank by vector
        vector_ranked = sorted(
            vector_score_map.items(), key=lambda x: -x[1]
        )
        vector_ranks = {}
        for rank, (obj_id, _) in enumerate(vector_ranked):
            vector_ranks[obj_id] = rank + 1

        # Combine via RRF
        rrf_scores = []
        for i, obj in enumerate(all_objects):
            obj_id = str(obj.id)
            bm25_rrf = 1.0 / (RRF_K + bm25_ranks.get(obj_id, RRF_K + len(all_objects)))
            hnsw_rrf = 1.0 / (RRF_K + vector_ranks.get(obj_id, RRF_K + len(all_objects)))
            combined = alpha * bm25_rrf + (1 - alpha) * hnsw_rrf
            rrf_scores.append((obj, combined))

        # Sort and return top_k
        rrf_scores.sort(key=lambda x: -x[1])
        top = rrf_scores[:top_k]

        return [
            {
                "id": str(obj.id),
                "exchange_core": obj.exchange_core,
                "specific_context": obj.specific_context,
                "room_assignments": obj.room_assignments,
                "score": round(score, 6),
            }
            for obj, score in top
        ]

    async def retrieve_context(
        self,
        db: AsyncSession,
        query: str,
        session_id: str,
        max_items: int = 5,
    ) -> list[dict]:
        """Retrieve relevant context for the current conversation turn."""
        results = await self.hybrid_search(db, query, session_id, top_k=max_items)
        return results


_retriever: Retriever | None = None


def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever
