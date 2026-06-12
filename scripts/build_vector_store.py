from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "src"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build persistent Maintenance Wizard vector store.")
    parser.add_argument("--vector-db", choices=["chromadb", "qdrant"], default=os.getenv("VECTOR_DB", "chromadb"))
    parser.add_argument("--embedding-model", default=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
    parser.add_argument("--real-model", action="store_true", help="Use sentence-transformers model instead of deterministic fallback.")
    parser.add_argument("--force", action="store_true", help="Force vector indexing even when AUTO_INDEX_VECTOR_STORE is false.")
    args = parser.parse_args()

    os.environ["VECTOR_DB"] = args.vector_db
    os.environ["EMBEDDING_MODEL"] = args.embedding_model
    os.environ["AUTO_INDEX_VECTOR_STORE"] = "true" if args.force or args.real_model else os.getenv("AUTO_INDEX_VECTOR_STORE", "true")
    if args.real_model:
        os.environ["ENABLE_RUNTIME_MODEL_LOADING"] = "true"
        os.environ["EAGER_LOAD_AI_MODELS"] = "true"

    from backend.rag.document_loader import chunk_documents, load_documents
    from backend.rag.pipeline import RagPipeline
    from backend.config import settings

    pipeline = RagPipeline()
    started = time.perf_counter()
    documents = load_documents()
    chunks = chunk_documents(documents)
    pipeline.ensure_index()
    status = pipeline.health_status("maintenance failure")
    vector_store = status["vector_store"]
    expected_collection = vector_store.get("expected_collection") or f"maintenance_knowledge_d{vector_store.get('embedding_dimension') or 384}"
    print(
        json.dumps(
            {
            "vector_db": args.vector_db,
            "embedding_model": args.embedding_model,
            "persist_directory": settings.chroma_path,
            "expected_collection": expected_collection,
            "actual_collection": vector_store.get("collection"),
            "embedding_dimension": vector_store.get("embedding_dimension"),
            "collection_name": vector_store.get("collection"),
            "document_count": vector_store.get("document_count", 0),
            "vector_count": status["vectors"],
            "source_documents": len(documents),
            "chunks": len(chunks),
            "build_time_ms": round((time.perf_counter() - started) * 1000, 2),
            "vector_store": vector_store,
            "embedding_service": status["embedding_service"],
            "hybrid_search": status.get("hybrid_search"),
        },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
