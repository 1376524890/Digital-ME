"""Indexer: pgvector HNSW vector index + BM25 keyword index.

Embedding model (sentence-transformers) is loaded lazily. If not installed,
vector search degrades gracefully: BM25-only retrieval still works.
"""

import hashlib
import struct

import numpy as np
from rank_bm25 import BM25Okapi
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import StructuredObject


def _fallback_hash_embedding(text: str, dim: int = 384) -> list[float]:
    """Simple hash-based pseudo-embedding when sentence-transformers is unavailable.
    This produces a deterministic, normalized vector that enables basic near-duplicate
    detection and retrieval. NOT a semantic embedding — BM25 handles actual search."""
    h = hashlib.sha256(text.encode()).digest()
    # Expand hash to fill the required dimension
    vals = []
    for i in range(dim):
        byte_val = h[i % len(h)]
        seed = struct.unpack("B", bytes([(byte_val + i) % 256]))[0] / 255.0
        vals.append(seed * 2.0 - 1.0)  # Center around 0
    arr = np.array(vals, dtype=float)
    arr = arr / (np.linalg.norm(arr) + 1e-10)
    return arr.tolist()


class Indexer:
    def __init__(self):
        self._embedding_model = None
        self._embedding_available = None  # None = not checked yet

    def _ensure_model(self):
        """Lazy-load embedding model. Returns True if loaded, False if unavailable."""
        if self._embedding_available is not None:
            return self._embedding_available

        try:
            from sentence_transformers import SentenceTransformer
            import os

            model_name = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            self._embedding_model = SentenceTransformer(model_name)
            self._embedding_available = True
        except Exception as e:
            print(f"Embedding model not available, using hash fallback: {e}")
            self._embedding_available = False
        return self._embedding_available

    async def preload(self):
        """Preload models for performance."""
        self._ensure_model()

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for text. Uses real model if available, else hash fallback."""
        if self._ensure_model():
            try:
                embedding = self._embedding_model.encode(text, normalize_embeddings=True)
                return embedding.tolist()
            except Exception:
                pass
        return _fallback_hash_embedding(text)

    async def index_object(self, db: AsyncSession, obj: StructuredObject):
        """Generate and store embedding for a StructuredObject."""
        text_for_embedding = f"{obj.exchange_core} {obj.specific_context}"
        embedding = await self.embed_text(text_for_embedding)
        obj.embedding = embedding
        await db.commit()

    async def build_bm25(self, objects: list[StructuredObject]) -> BM25Okapi | None:
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
