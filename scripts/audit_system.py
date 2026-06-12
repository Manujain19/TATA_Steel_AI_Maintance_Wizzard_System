from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "src"))


def main() -> None:
    backend_main = (ROOT_DIR / "backend" / "main.py").read_text(encoding="utf-8")
    frontend = (ROOT_DIR / "web" / "app.js").read_text(encoding="utf-8")
    routes = sorted(set(re.findall(r'@app\.(?:get|post|websocket)\("([^"]+)"', backend_main)))
    frontend_calls = sorted(set(re.findall(r'(?:api|apiWithTimeout)\("([^"]+)"', frontend)))
    dependencies = {
        name: bool(importlib.util.find_spec(name))
        for name in ["fastapi", "uvicorn", "chromadb", "qdrant_client", "sentence_transformers", "langgraph", "langsmith"]
    }
    try:
        from backend.caches import RAGPipelineCache, LangGraphWorkflowCache

        rag = RAGPipelineCache.get()
        workflow = LangGraphWorkflowCache.get()
        vector_status = rag.vector_store.status()
        workflow_status = workflow.health_status()
        embedding_status = rag.embedding_service.health_status()
        reranker_status = rag.reranker.health_status()
    except Exception as exc:
        vector_status = {"error": str(exc)}
        workflow_status = {"error": str(exc)}
        embedding_status = {"error": str(exc)}
        reranker_status = {"error": str(exc)}
    print(
        json.dumps(
            {
                "api_routes": routes,
                "frontend_api_calls": frontend_calls,
                "dependencies": dependencies,
                "vector_store": vector_status,
                "workflow": workflow_status,
                "embedding_service": embedding_status,
                "reranker": reranker_status,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
