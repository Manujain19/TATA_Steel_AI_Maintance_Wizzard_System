from __future__ import annotations

import logging
import time
import hashlib
import threading
from typing import Dict, List

from backend.embeddings.service import EmbeddingService
from backend.config import settings
from backend.rag.document_loader import chunk_documents, load_documents
from backend.rag.hybrid_retriever import BM25Retriever, Reranker
from backend.telemetry.observability import metrics
from backend.vectorstores.factory import build_vector_store

logger = logging.getLogger(__name__)


class RagPipeline:
    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.vector_store = build_vector_store()
        self.reranker = Reranker()
        self.documents: List[Dict] = []
        self.bm25: BM25Retriever | None = None
        self.indexed = False
        self._index_lock = threading.RLock()
        self.last_retrieval_stats: Dict = {}
        self.retrieval_cache: Dict[str, Dict] = {}
        self.retrieval_cache_ttl_seconds = 15 * 60

    def ensure_index(self) -> None:
        if self.indexed:
            return
        with self._index_lock:
            if self.indexed:
                return
            with metrics.span("rag_index_documents"):
                chunks = chunk_documents(load_documents())
                self.documents = chunks
                self.bm25 = BM25Retriever(chunks)
                status = self._store_status()
                if status.get("document_count", 0) > 0 and not settings.auto_index_vector_store:
                    logger.info(
                        "RAG index already available collection=%s document_count=%s",
                        status.get("collection"),
                        status.get("document_count"),
                    )
                    self.indexed = True
                    return
                if not settings.auto_index_vector_store:
                    logger.info(
                        "Vector auto-index disabled; using BM25/hybrid fallback until scripts/build_vector_store.py is run"
                    )
                    self.indexed = True
                    return
                self.embedding_service.index_documents(self.vector_store, chunks)
                logger.info(
                    "RAG indexed documents collection=%s chunks=%s embedding_model=%s",
                    self._store_status().get("collection"),
                    len(chunks),
                    self.embedding_service.model_name,
                )
                self.indexed = True

    def retrieve(self, query: str, equipment_id: str | None = None, top_k: int = 6) -> List[Dict]:
        self.ensure_index()
        cache_key = self._cache_key(query, equipment_id, top_k)
        cached_entry = self.retrieval_cache.get(cache_key)
        if cached_entry and (time.time() - float(cached_entry.get("created_at", 0))) <= self.retrieval_cache_ttl_seconds:
            cached = cached_entry.get("results", [])
            self.last_retrieval_stats = {
                **self.last_retrieval_stats,
                "cache_hit": True,
                "retrieval_time_ms": 0,
                "reranking_time_ms": 0,
                "reranked_results": len(cached),
            }
            return cached
        if cached_entry:
            self.retrieval_cache.pop(cache_key, None)
        filters = {"equipment_id": equipment_id} if equipment_id else {}
        retrieval_started = time.perf_counter()
        with metrics.span("rag_retrieval"):
            vector_results = []
            if self._store_status().get("document_count", 0) > 0:
                vector_results = self.embedding_service.semantic_search(self.vector_store, query, top_k=top_k * 4, filters=filters)
            bm25_results = self.bm25.search(query, top_k=top_k * 2, filters=filters) if self.bm25 else []
        if not vector_results and equipment_id:
            if self._store_status().get("document_count", 0) > 0:
                vector_results = self.embedding_service.semantic_search(self.vector_store, query, top_k=top_k * 4)
        if not bm25_results and equipment_id and self.bm25:
            bm25_results = self.bm25.search(query, top_k=top_k * 2)
        merged = self._merge_results(vector_results, bm25_results)
        rerank_started = time.perf_counter()
        rerank_candidates = min(5, len(merged))
        rerank_skipped = len(vector_results) == 0
        if rerank_skipped:
            results = merged[: min(5, top_k)]
        else:
            with metrics.span("rag_reranking"):
                results = self.reranker.rerank(query, merged[:rerank_candidates], top_k=min(5, top_k), asset_id=equipment_id)
        retrieval_ms = round((time.perf_counter() - retrieval_started) * 1000, 2)
        rerank_ms = round((time.perf_counter() - rerank_started) * 1000, 2)
        hybrid_score = round(sum(float(item.get("hybrid_score", 0) or 0) for item in results) / max(1, len(results)), 4)
        self.last_retrieval_stats = {
            "hybrid_retrieval_score": hybrid_score,
            "reranking_time_ms": rerank_ms,
            "retrieval_time_ms": retrieval_ms,
            "cache_hit": False,
            "rerank_candidates": rerank_candidates,
            "rerank_skipped": rerank_skipped,
            "bm25_results": len(bm25_results),
            "vector_results": len(vector_results),
            "merged_results": len(merged),
            "reranked_results": len(results),
            "reranker": self.reranker.health_status(),
            "embedding": self.embedding_service.health_status(),
        }
        logger.info(
            "Hybrid RAG retrieval query=%r equipment_id=%s bm25=%s vector=%s retrieved_documents=%s hybrid_score=%s rerank_ms=%s top_score=%s",
            query[:120],
            equipment_id,
            len(bm25_results),
            len(vector_results),
            len(results),
            hybrid_score,
            rerank_ms,
            results[0].get("score") if results else None,
        )
        self.retrieval_cache[cache_key] = {"created_at": time.time(), "results": results}
        return results

    def assemble_context(self, query: str, equipment_id: str | None = None, top_k: int = 6) -> Dict:
        retrieved = self.retrieve(query, equipment_id, top_k=top_k)
        return {
            "query": query,
            "equipment_id": equipment_id,
            "documents": retrieved,
            "context_text": "\n\n".join(item["text"] for item in retrieved),
            "hybrid_retrieval": self.last_retrieval_stats,
        }

    def _merge_results(self, vector_results: List[Dict], bm25_results: List[Dict]) -> List[Dict]:
        merged: Dict[str, Dict] = {}
        rrf_k = 60.0
        for rank, item in enumerate(vector_results, start=1):
            score = 1.0 / (rrf_k + rank)
            merged[item["id"]] = {
                **item,
                "vector_score": round(float(item.get("score", 0) or 0), 4),
                "bm25_score": 0.0,
                "rrf_score": round(score, 6),
                "hybrid_score": round(score, 6),
            }
        for rank, item in enumerate(bm25_results, start=1):
            score = 1.0 / (rrf_k + rank)
            existing = merged.get(item["id"], item)
            existing_rrf = float(existing.get("rrf_score", 0) or 0)
            merged[item["id"]] = {
                **existing,
                **item,
                "vector_score": existing.get("vector_score", 0.0),
                "bm25_score": round(float(item.get("bm25_score", 0) or 0), 4),
                "rrf_score": round(existing_rrf + score, 6),
                "hybrid_score": round(existing_rrf + score, 6),
            }
        return sorted(merged.values(), key=lambda item: item.get("hybrid_score", 0), reverse=True)

    def _store_status(self) -> Dict:
        status = getattr(self.vector_store, "status", None)
        if callable(status):
            return status()
        return {"backend": type(self.vector_store).__name__, "document_count": 0, "available": False}

    def health_status(self) -> Dict:
        documents = load_documents()
        chunks = chunk_documents(documents)
        self.ensure_index()
        store = self._store_status()
        store_ready = bool(store.get("available") or store.get("ready") or store.get("document_count", 0) > 0)
        return {
            "status": "healthy" if store_ready else "degraded",
            "documents": len(documents),
            "vectors": store.get("document_count", len(chunks)),
            "chunks": len(chunks),
            "vector_store": store,
            "retrieved_chunks": 0,
            "top_similarity_score": None,
            "embedding_model": self.embedding_service.model_name,
            "embedding_service": self.embedding_service.health_status(),
            "hybrid_search": {
                "status": "metadata_only",
                **self.last_retrieval_stats,
                "retrieval_test": "not_run",
            },
            "reranker": self.reranker.health_status(),
            "cache": {
                "retrieval_cache_entries": len(self.retrieval_cache),
                "embedding_cache_entries": self.embedding_service.health_status().get("cache_size", 0),
            },
        }

    def _cache_key(self, query: str, equipment_id: str | None, top_k: int) -> str:
        raw = f"{equipment_id or ''}|{int(top_k)}|{query.strip().lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
