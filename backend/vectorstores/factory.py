from __future__ import annotations

import logging

from backend.config import settings
from backend.vectorstores.chroma_store import ChromaVectorStore

logger = logging.getLogger(__name__)


def build_vector_store():
    if settings.vector_db == "qdrant":
        from backend.vectorstores.qdrant_store import QdrantVectorStore

        qdrant = QdrantVectorStore()
        if qdrant.status().get("available"):
            return qdrant
        logger.warning("Qdrant unavailable; falling back to ChromaDB vector store")
        return ChromaVectorStore()
    logger.info("Vector store backend selected: chromadb")
    return ChromaVectorStore()
