"""Indexer: pgvector HNSW vector index + BM25 keyword index."""

import numpy as np
from rank_bm25 import BM25Okapi
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import StructuredObject


class Indexer:
    def __init__(self):
        self._embedding_model = None

    @property
    def embedding_model(self):
        if self._embedding_model is None:
            from sentence_transformers import SentenceTransformer
            import os
            model_name = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            self._embedding_model = SentenceTransformer(model_name)
        return self._embedding_model

    async def embed_text(self, text: str) -> list[float]:
        """Generate 384-dim embedding for a text."""
        model = self.embedding_model
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    async def index_object(self, db: AsyncSession, obj: StructuredObject):
        """Generate and store embedding for a StructuredObject."""
        text_for_embedding = f"{obj.exchange_core} {obj.specific_context}"
        embedding = await self.embed_text(text_for_embedding)
        obj.embedding = embedding
        await db.commit()

    async def build_bm25(self, objects: list[StructuredObject]) -> BM25Okapi:
        """Build BM25 index from structured objects."""
        corpus = []
        for obj in objects:
            doc = f"{obj.exchange_core} {obj.specific_context}"
            corpus.append(doc.lower().split())
        return BM25Okapi(corpus) if corpus else None

    async def vector_search(
        self, db: AsyncSession, query: str, session_id: str, top_k: int = 20
    ) -> list[tuple[StructuredObject, float]]:
        """HNSW vector similarity search on pgvector."""
        query_embedding = await self.embed_text(query)
        embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"

        result = await db.execute(
            text("""
                SELECT id, 1 - (embedding <=> :embedding::vector) AS similarity
                FROM structured_objects
                WHERE session_id = :session_id
                AND embedding IS NOT NULL
                ORDER BY embedding <=> :embedding::vector
                LIMIT :top_k
            """),
            {
                "embedding": embedding_str,
                "session_id": session_id,
                "top_k": top_k,
            },
        )
        results = []
        for row in result:
            obj = await db.get(StructuredObject, row.id)
            if obj:
                results.append((obj, float(row.similarity)))
        return results


_indexer: Indexer | None = None


def get_indexer() -> Indexer:
    global _indexer
    if _indexer is None:
        _indexer = Indexer()
    return _indexer
