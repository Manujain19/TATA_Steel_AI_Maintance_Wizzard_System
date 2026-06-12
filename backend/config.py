from __future__ import annotations

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "outputs"


class Settings:
    app_name = "Maintenance Wizard - Tata Steel AI Platform"
    llm_provider = os.getenv("LLM_PROVIDER", os.getenv("STEELMIND_PROVIDER", "groq"))
    vector_db = os.getenv("VECTOR_DB", "chromadb").lower()
    database_url = os.getenv("DATABASE_URL", "postgresql://maintenance:maintenance@postgres:5432/maintenance_wizard")
    chroma_path = os.getenv("CHROMA_PATH", str(ROOT_DIR / ".vectorstores" / "chromadb"))
    qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
    embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    reranker_model = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    model_mode = os.getenv("MODEL_MODE", "offline").lower()
    _model_cache_dir = Path(os.getenv("MODEL_CACHE_DIR", str(ROOT_DIR / ".model_cache")))
    model_cache_dir = str(_model_cache_dir if _model_cache_dir.is_absolute() else ROOT_DIR / _model_cache_dir)
    allow_model_fallback = os.getenv("ALLOW_MODEL_FALLBACK", "false").lower() == "true"
    eager_load_ai_models = os.getenv("EAGER_LOAD_AI_MODELS", "false").lower() == "true"
    enable_runtime_model_loading = os.getenv("ENABLE_RUNTIME_MODEL_LOADING", "true").lower() == "true"
    auto_index_vector_store = os.getenv("AUTO_INDEX_VECTOR_STORE", "false").lower() == "true"
    background_preload_ai_models = os.getenv(
        "BACKGROUND_PRELOAD",
        os.getenv("BACKGROUND_PRELOAD_AI_MODELS", "true"),
    ).lower() == "true"
    llm_fail_fast = os.getenv("LLM_FAIL_FAST", "false").lower() == "true"
    enable_langsmith = os.getenv("LANGSMITH_TRACING", os.getenv("LANGCHAIN_TRACING_V2", "false")).lower() == "true"
    enable_postgres = os.getenv("ENABLE_POSTGRES", "false").lower() == "true"
    enable_langgraph = os.getenv("ENABLE_LANGGRAPH", "true").lower() == "true"


settings = Settings()
