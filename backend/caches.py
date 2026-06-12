from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.agents.langgraph_workflow import MaintenanceLangGraphWorkflow
    from backend.embeddings.service import EmbeddingService
    from backend.rag.hybrid_retriever import Reranker
    from backend.rag.pipeline import RagPipeline


class EmbeddingModelCache:
    @staticmethod
    @lru_cache(maxsize=4)
    def get(model_name: str | None = None) -> "EmbeddingService":
        from backend.embeddings.service import EmbeddingService

        return EmbeddingService(model_name=model_name)


class RerankerCache:
    @staticmethod
    @lru_cache(maxsize=4)
    def get(model_name: str | None = None) -> "Reranker":
        from backend.rag.hybrid_retriever import Reranker

        return Reranker(model_name=model_name)


class ChromaCache:
    @staticmethod
    @lru_cache(maxsize=1)
    def get():
        from backend.vectorstores.factory import build_vector_store

        return build_vector_store()


class QdrantCache:
    @staticmethod
    @lru_cache(maxsize=1)
    def get():
        from backend.vectorstores.factory import build_vector_store

        return build_vector_store()


class RAGPipelineCache:
    @staticmethod
    @lru_cache(maxsize=1)
    def get() -> "RagPipeline":
        from backend.rag.pipeline import RagPipeline

        return RagPipeline()


class LangGraphWorkflowCache:
    @staticmethod
    @lru_cache(maxsize=1)
    def get() -> "MaintenanceLangGraphWorkflow":
        from backend.agents.langgraph_workflow import MaintenanceLangGraphWorkflow

        return MaintenanceLangGraphWorkflow(rag=RAGPipelineCache.get())


class ToolAgentCache:
    @staticmethod
    @lru_cache(maxsize=1)
    def get_workflow() -> "MaintenanceLangGraphWorkflow":
        return LangGraphWorkflowCache.get()
