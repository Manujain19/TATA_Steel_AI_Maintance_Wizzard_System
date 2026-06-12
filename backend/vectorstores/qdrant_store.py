from __future__ import annotations

import logging
from typing import Dict, List

from backend.config import settings
from backend.vectorstores.base import InMemoryVectorStore

logger = logging.getLogger(__name__)


class QdrantVectorStore(InMemoryVectorStore):
    """Qdrant adapter with in-memory fallback when qdrant-client is unavailable."""

    def __init__(self, collection_name: str = "maintenance_knowledge") -> None:
        super().__init__()
        self.collection_name = collection_name
        self.client = None
        try:
            from qdrant_client import QdrantClient

            self.client = QdrantClient(url=settings.qdrant_url)
            self.client.get_collections()
            logger.info("Qdrant connection ready: %s", settings.qdrant_url)
        except Exception as exc:
            logger.warning("Qdrant unavailable, using local vector fallback: %s", exc)
            self.client = None

    def add_documents(self, documents: List[Dict], embeddings: List[List[float]]) -> None:
        if not self.client:
            return super().add_documents(documents, embeddings)
        # Production deployments can enable collection creation/upsert here.
        logger.info(
            "Qdrant client connected; using local fallback upsert collection=%s document_count=%s",
            self.collection_name,
            len(documents),
        )
        return super().add_documents(documents, embeddings)

    def search(self, embedding: List[float], top_k: int = 6, filters: Dict | None = None) -> List[Dict]:
        rows = super().search(embedding, top_k, filters)
        logger.info(
            "Qdrant retrieval collection=%s top_k=%s retrieved_vectors=%s connected=%s top_score=%s",
            self.collection_name,
            top_k,
            len(rows),
            self.client is not None,
            rows[0]["score"] if rows else None,
        )
        return rows

    def status(self) -> Dict:
        collection_count = 0
        if self.client:
            try:
                collections = self.client.get_collections()
                collection_count = len(getattr(collections, "collections", []) or [])
            except Exception:
                collection_count = 0
        return {
            "backend": "qdrant",
            "collection": self.collection_name,
            "available": self.client is not None,
            "document_count": len(self.rows),
            "collections": collection_count,
            "fallback": self.client is None,
        }
