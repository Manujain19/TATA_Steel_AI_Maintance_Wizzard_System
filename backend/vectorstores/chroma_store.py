from __future__ import annotations

import logging
import os
import threading
import time
import traceback
from typing import Dict, List

from backend.config import settings
from backend.utils.numpy_compat import apply_numpy_compat
from backend.vectorstores.base import InMemoryVectorStore

logger = logging.getLogger(__name__)


class ChromaVectorStore(InMemoryVectorStore):
    """ChromaDB adapter with in-memory fallback when chromadb is unavailable."""

    _client_lock = threading.RLock()
    _clients: Dict[str, object] = {}
    _client_tracebacks: Dict[str, str] = {}

    def __init__(self, collection_name: str = "maintenance_knowledge") -> None:
        super().__init__()
        self.base_collection_name = collection_name
        self.collection_name = collection_name
        self.collection = None
        self.client = None
        self.embedding_dimension = None
        self.detected_collections: List[Dict] = []
        self.initialization_error = None
        self.initialization_traceback = None
        self.last_query_error = None
        self.last_query_traceback = None
        self.last_add_error = None
        self.last_add_traceback = None
        self.last_list_error = None
        self.last_list_traceback = None
        self._status_cache: Dict | None = None
        self._status_cache_at = 0.0
        self._status_cache_ttl_seconds = 5
        self._last_reconnect_attempt = 0.0
        self._reconnect_interval_seconds = 2.0
        self.expected_collection = self._target_collection_name(expected_embedding_dimension(settings.embedding_model))
        logger.info(
            "EXPECTED_COLLECTION=%s ACTUAL_COLLECTION=%s PERSIST_DIRECTORY=%s EMBEDDING_DIMENSION=%s",
            self.expected_collection,
            self.collection_name,
            settings.chroma_path,
            expected_embedding_dimension(settings.embedding_model),
        )
        self._connect()

    def _connect(self) -> None:
        try:
            self.client = self._get_client()
            self.detected_collections = self._list_collections()
            self._use_dimension_collection(expected_embedding_dimension(settings.embedding_model), force=True)
            logger.info(
                "ChromaDB collection ready EXPECTED_COLLECTION=%s ACTUAL_COLLECTION=%s PERSIST_DIRECTORY=%s document_count=%s",
                self.expected_collection,
                self.collection_name,
                settings.chroma_path,
                self._count(),
            )
        except Exception as exc:
            self.initialization_error = str(exc)
            self.initialization_traceback = traceback.format_exc()
            logger.warning(
                "ChromaDB unavailable, using in-memory vector fallback EXPECTED_COLLECTION=%s ACTUAL_COLLECTION=%s PERSIST_DIRECTORY=%s error=%s traceback=%s",
                self.expected_collection,
                self.collection_name,
                settings.chroma_path,
                exc,
                self.initialization_traceback,
            )
            self.collection = None
            self._status_cache = None

    @classmethod
    def _get_client(cls):
        path = str(settings.chroma_path)
        with cls._client_lock:
            cached = cls._clients.get(path)
            if cached is not None:
                logger.info("CHROMA_CLIENT_CACHE_HIT PERSIST_DIRECTORY=%s", path)
                return cached
            try:
                apply_numpy_compat()
                os.makedirs(path, exist_ok=True)
                os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
                os.environ.setdefault("CHROMA_TELEMETRY", "False")
                os.environ.setdefault("CHROMA_SERVER_ANONYMIZED_TELEMETRY", "False")
                import chromadb

                try:
                    from chromadb.config import Settings as ChromaSettings

                    client = chromadb.PersistentClient(
                        path=path,
                        settings=ChromaSettings(anonymized_telemetry=False),
                    )
                except TypeError:
                    client = chromadb.PersistentClient(path=path)
                cls._clients[path] = client
                cls._client_tracebacks.pop(path, None)
                logger.info("CHROMA_CLIENT_CREATED PERSIST_DIRECTORY=%s", path)
                return client
            except Exception:
                cls._client_tracebacks[path] = traceback.format_exc()
                logger.warning(
                    "CHROMA_CLIENT_CREATE_FAILED PERSIST_DIRECTORY=%s traceback=%s",
                    path,
                    cls._client_tracebacks[path],
                )
                raise

    def ensure_chromadb(self) -> bool:
        if self.collection and self._count() > 0:
            return True
        now = time.time()
        if now - self._last_reconnect_attempt < self._reconnect_interval_seconds:
            return bool(self.collection and self._count() > 0)
        self._last_reconnect_attempt = now
        logger.info(
            "Retrying ChromaDB connection EXPECTED_COLLECTION=%s ACTUAL_COLLECTION=%s PERSIST_DIRECTORY=%s",
            self.expected_collection,
            self.collection_name,
            settings.chroma_path,
        )
        self._connect()
        return bool(self.collection and self._count() > 0)

    def is_ready(self) -> bool:
        return self.ensure_chromadb()

    def add_documents(self, documents: List[Dict], embeddings: List[List[float]]) -> None:
        dimension = len(embeddings[0]) if embeddings else None
        if dimension:
            self._use_dimension_collection(dimension)
        if not self.collection:
            return super().add_documents(documents, embeddings)
        existing = self._count()
        if existing:
            logger.info("ChromaDB collection %s already indexed with %s documents", self.collection_name, existing)
            return
        try:
            self.collection.add(
                ids=[doc["id"] for doc in documents],
                documents=[doc["text"] for doc in documents],
                metadatas=[doc.get("metadata", {}) for doc in documents],
                embeddings=embeddings,
            )
            self._status_cache = None
            logger.info("ChromaDB indexed collection=%s document_count=%s", self.collection_name, len(documents))
        except Exception as exc:
            self.last_add_error = str(exc)
            self.last_add_traceback = traceback.format_exc()
            logger.warning("ChromaDB add failed, using in-memory fallback: %s traceback=%s", exc, self.last_add_traceback)
            return super().add_documents(documents, embeddings)

    def search(self, embedding: List[float], top_k: int = 6, filters: Dict | None = None) -> List[Dict]:
        self._use_dimension_collection(len(embedding))
        if not self.collection:
            self.ensure_chromadb()
        if not self.collection:
            rows = super().search(embedding, top_k, filters)
            logger.info(
                "Chroma fallback retrieval collection=%s top_k=%s retrieved_chunks=%s",
                self.collection_name,
                top_k,
                len(rows),
            )
            return rows
        try:
            result = self.collection.query(query_embeddings=[embedding], n_results=top_k, where=filters or None)
        except Exception as exc:
            mismatch = self._dimension_mismatch(exc)
            if mismatch:
                logger.warning(
                    "ChromaDB dimension mismatch detected collection=%s expected=%s runtime=%s; switching collection",
                    self.collection_name,
                    mismatch.get("expected"),
                    mismatch.get("runtime"),
                )
                self._use_dimension_collection(mismatch["runtime"], force=True)
                if self.collection and self._count() > 0:
                    try:
                        result = self.collection.query(query_embeddings=[embedding], n_results=top_k, where=filters or None)
                    except Exception as second_exc:
                        self.last_query_error = str(second_exc)
                        self.last_query_traceback = traceback.format_exc()
                        logger.warning("ChromaDB dimension-correct retry failed: %s traceback=%s", second_exc, self.last_query_traceback)
                        return super().search(embedding, top_k, filters)
                else:
                    return super().search(embedding, top_k, filters)
            else:
                self.last_query_error = str(exc)
                self.last_query_traceback = traceback.format_exc()
                logger.warning("ChromaDB query failed, using in-memory fallback: %s traceback=%s", exc, self.last_query_traceback)
                return super().search(embedding, top_k, filters)
        rows = []
        for idx, doc_id in enumerate(result.get("ids", [[]])[0]):
            rows.append(
                {
                    "id": doc_id,
                    "text": result.get("documents", [[]])[0][idx],
                    "metadata": result.get("metadatas", [[]])[0][idx],
                    "score": result.get("distances", [[0]])[0][idx],
                }
            )
        logger.info(
            "ChromaDB retrieval collection=%s document_count=%s retrieved_chunks=%s top_score=%s",
            self.collection_name,
            self._count(),
            len(rows),
            rows[0]["score"] if rows else None,
        )
        return rows

    def _count(self) -> int:
        if not self.collection:
            return len(self.rows)
        try:
            return int(self.collection.count())
        except Exception:
            return 0

    def status(self) -> Dict:
        ready = self.is_ready()
        now = time.time()
        if ready and self._status_cache and now - self._status_cache_at <= self._status_cache_ttl_seconds:
            return self._status_cache
        document_count = self._count()
        self._status_cache = {
            "backend": "chromadb" if self.collection else "in_memory",
            "collection": self.collection_name,
            "expected_collection": self.expected_collection,
            "base_collection": self.base_collection_name,
            "available": self.collection is not None,
            "ready": ready,
            "document_count": document_count,
            "fallback": self.collection is None,
            "initialization_error": self.initialization_error,
            "initialization_traceback": self.initialization_traceback,
            "last_query_error": self.last_query_error,
            "last_query_traceback": self.last_query_traceback,
            "last_add_error": self.last_add_error,
            "last_add_traceback": self.last_add_traceback,
            "last_list_error": self.last_list_error,
            "last_list_traceback": self.last_list_traceback,
            "embedding_dimension": self.embedding_dimension,
            "dimension_strategy": "versioned_collection_per_embedding_dimension",
            "persist_directory": settings.chroma_path,
            "client_cached": str(settings.chroma_path) in self._clients,
            "client_initialization_traceback": self._client_tracebacks.get(str(settings.chroma_path)),
            "detected_collections": self._list_collections(),
        }
        self._status_cache_at = now
        return self._status_cache

    def _use_dimension_collection(self, dimension: int, force: bool = False) -> None:
        if not self.client:
            return
        target = self._target_collection_name(dimension)
        self.expected_collection = target
        if not force and self.collection and self.collection_name == target:
            return
        try:
            try:
                self.collection = self.client.get_collection(target)
            except Exception as get_exc:
                if not settings.auto_index_vector_store:
                    self.collection = None
                    self.collection_name = target
                    self.embedding_dimension = dimension
                    self.initialization_error = str(get_exc)
                    self.initialization_traceback = traceback.format_exc()
                    self._status_cache = None
                    logger.warning(
                        "Expected ChromaDB collection is not available EXPECTED_COLLECTION=%s PERSIST_DIRECTORY=%s error=%s traceback=%s",
                        target,
                        settings.chroma_path,
                        get_exc,
                        self.initialization_traceback,
                    )
                    return
                self.collection = self.client.get_or_create_collection(
                    target,
                    metadata={"embedding_dimension": dimension, "base_collection": self.base_collection_name},
                )
            self.collection_name = target
            self.embedding_dimension = dimension
            self.initialization_error = None
            self.initialization_traceback = None
            self._status_cache = None
            logger.info(
                "Chroma collection selected EXPECTED_COLLECTION=%s ACTUAL_COLLECTION=%s PERSIST_DIRECTORY=%s document_count=%s",
                target,
                self.collection_name,
                settings.chroma_path,
                self._count(),
            )
        except Exception as exc:
            self.initialization_error = str(exc)
            self.initialization_traceback = traceback.format_exc()
            logger.warning("Unable to select ChromaDB dimension collection %s: %s traceback=%s", target, exc, self.initialization_traceback)

    def _target_collection_name(self, dimension: int) -> str:
        return f"{self.base_collection_name}_d{dimension}"

    def _dimension_mismatch(self, exc: Exception) -> Dict | None:
        import re

        text = str(exc)
        match = re.search(r"expecting embedding with dimension (\d+), got (\d+)", text, re.IGNORECASE)
        if not match:
            return None
        return {"expected": int(match.group(1)), "runtime": int(match.group(2))}

    def _list_collections(self) -> List[Dict]:
        if not self.client:
            return []
        rows = []
        try:
            for collection in self.client.list_collections():
                name = getattr(collection, "name", str(collection))
                try:
                    current = self.client.get_collection(name)
                    count = int(current.count())
                    metadata = getattr(current, "metadata", None) or {}
                except Exception:
                    count = 0
                    metadata = {}
                rows.append({"name": name, "document_count": count, "metadata": metadata})
        except Exception as exc:
            self.last_list_error = str(exc)
            self.last_list_traceback = traceback.format_exc()
            logger.warning("Unable to list ChromaDB collections: %s traceback=%s", exc, self.last_list_traceback)
            return []
        return rows


def expected_embedding_dimension(model_name: str) -> int:
    dimensions = {
        "all-MiniLM-L6-v2": 384,
        "sentence-transformers/all-MiniLM-L6-v2": 384,
        "BAAI/bge-large-en-v1.5": 1024,
        "nomic-embed-text": 768,
    }
    return dimensions.get(model_name, 384)
