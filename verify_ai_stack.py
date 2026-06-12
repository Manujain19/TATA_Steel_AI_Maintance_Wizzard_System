from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "src"))


def safe_status(name: str, fn):
    started = time.perf_counter()
    try:
        value = fn()
        if isinstance(value, dict):
            value.setdefault("ok", True)
            value.setdefault("latency_ms", round((time.perf_counter() - started) * 1000, 2))
        return value
    except Exception as exc:
        return {
            "ok": False,
            "status": "error",
            "component": name,
            "error": str(exc),
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }


def model_path(model) -> str | None:
    if model is None:
        return None
    for attr in ("cache_folder", "model_name_or_path"):
        value = getattr(model, attr, None)
        if value:
            return str(value)
    modules = getattr(model, "_modules", None)
    if isinstance(modules, dict):
        for module in modules.values():
            auto_model = getattr(module, "auto_model", None)
            value = getattr(getattr(auto_model, "config", None), "_name_or_path", None)
            if value:
                return str(value)
    return str(type(model).__name__)


def verify_groq(run_test: bool) -> dict:
    from services.llm_provider import LLMProvider

    provider = LLMProvider()
    status = provider.diagnostic_status(run_test=run_test)
    return {
        "provider": status.get("provider"),
        "model": status.get("model"),
        "api_key_loaded": status.get("api_key_loaded"),
        "connection_status": status.get("connection_status"),
        "error": status.get("error") or status.get("last_status", {}).get("error"),
        "last_status": status.get("last_status", {}),
    }


def verify_langgraph() -> dict:
    from backend.agents.langgraph_workflow import MaintenanceLangGraphWorkflow

    workflow = MaintenanceLangGraphWorkflow()
    status = workflow.health_status()
    return {
        "status": status.get("status"),
        "engine": status.get("engine"),
        "nodes": status.get("nodes", []),
        "langgraph_active": status.get("engine") == "langgraph",
    }


def verify_embedding() -> dict:
    from backend.embeddings.service import EmbeddingService

    service = EmbeddingService("all-MiniLM-L6-v2")
    service._load_model()
    vector = service.generate_embedding("maintenance failure root cause")
    status = service.health_status()
    return {
        "status": status.get("status"),
        "model": status.get("model"),
        "model_loaded": bool(service.model),
        "backend": status.get("backend"),
        "embedding_dimensions": len(vector),
        "configured_dimensions": status.get("dimensions"),
        "model_path": model_path(service.model),
        "load_attempted": status.get("load_attempted"),
    }


def verify_reranker() -> dict:
    from backend.rag.hybrid_retriever import Reranker

    reranker = Reranker("cross-encoder/ms-marco-MiniLM-L-6-v2")
    reranker._load_model()
    ranked = reranker.rerank(
        "hydraulic pressure failure",
        [
            {"id": "a", "text": "Hydraulic pressure dropped and seal leakage is suspected.", "score": 0.2},
            {"id": "b", "text": "Monthly inspection completed with normal vibration.", "score": 0.1},
        ],
        top_k=2,
        asset_id="VERIFY",
    )
    status = reranker.health_status()
    return {
        "status": status.get("status"),
        "model": status.get("model"),
        "model_loaded": bool(reranker.model),
        "backend": status.get("backend"),
        "model_path": model_path(reranker.model),
        "rerank_success": bool(ranked),
        "top_document": ranked[0]["id"] if ranked else None,
        "load_attempted": status.get("load_attempted"),
    }


def verify_chroma() -> dict:
    from backend.rag.pipeline import RagPipeline

    pipeline = RagPipeline()
    pipeline.ensure_index()
    store = pipeline.vector_store
    status = store.status()
    embedding = pipeline.embedding_service.generate_embedding("maintenance failure root cause")
    rows = store.search(embedding, top_k=3, filters={})
    refreshed = store.status()
    reason = None
    if refreshed.get("backend") != "chromadb":
        reason = (
            refreshed.get("initialization_error")
            or refreshed.get("last_query_error")
            or refreshed.get("last_add_error")
            or "ChromaDB client or collection is unavailable in this Python environment."
        )
    return {
        "backend": refreshed.get("backend"),
        "healthy": refreshed.get("backend") == "chromadb" and int(refreshed.get("document_count", 0) or 0) > 0 and bool(rows),
        "collection": refreshed.get("collection"),
        "expected_collection": "maintenance_knowledge_d384",
        "document_count": refreshed.get("document_count", 0),
        "vector_count": refreshed.get("document_count", 0),
        "dimension": refreshed.get("embedding_dimension"),
        "retrieval_test": "passed" if rows else "failed",
        "retrieved_count": len(rows),
        "fallback_reason": reason,
        "persist_directory": refreshed.get("persist_directory"),
        "detected_collections": refreshed.get("detected_collections", []),
        "initial_status": status,
    }


def verify_hybrid_rag() -> dict:
    from backend.rag.pipeline import RagPipeline

    pipeline = RagPipeline()
    rows = pipeline.retrieve("gearbox oil contamination bearing failure", "TSA-RM-GBX-002", top_k=6)
    stats = pipeline.last_retrieval_stats
    vector_status = pipeline.vector_store.status()
    reranker_status = pipeline.reranker.health_status()
    return {
        "status": "healthy" if rows else "degraded",
        "bm25_active": stats.get("bm25_results", 0) > 0,
        "chromadb_active": vector_status.get("backend") == "chromadb" and stats.get("vector_results", 0) > 0,
        "cross_encoder_active": reranker_status.get("backend") == "cross_encoder",
        "reranker_backend": reranker_status.get("backend"),
        "retrieved_documents": len(rows),
        "retrieval_stats": stats,
        "vector_store": vector_status,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Maintenance Wizard production AI stack.")
    parser.add_argument("--run-llm-test", action="store_true", help="Call Groq health generation test.")
    args = parser.parse_args()

    report = {
        "environment": {
            "python": sys.version.split()[0],
            "vector_db": os.getenv("VECTOR_DB", "chromadb"),
            "embedding_model": os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            "reranker_model": os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"),
            "hf_local_files_only": os.getenv("HF_LOCAL_FILES_ONLY", os.getenv("TRANSFORMERS_OFFLINE", "false")),
        },
        "groq_status": safe_status("groq", lambda: verify_groq(args.run_llm_test)),
        "langgraph_status": safe_status("langgraph", verify_langgraph),
        "embedding_status": safe_status("embedding", verify_embedding),
        "reranker_status": safe_status("reranker", verify_reranker),
        "chroma_status": safe_status("chroma", verify_chroma),
        "hybrid_rag_status": safe_status("hybrid_rag", verify_hybrid_rag),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
