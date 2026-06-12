from __future__ import annotations

import logging
import os
from typing import Any, Dict

from backend.config import settings
from backend.telemetry.observability import metrics

logger = logging.getLogger(__name__)


class LangSmithObserver:
    """Optional LangSmith facade with local metrics fallback."""

    def __init__(self) -> None:
        self.enabled = settings.enable_langsmith and bool(os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY"))
        self.project = os.getenv("LANGSMITH_PROJECT", os.getenv("LANGCHAIN_PROJECT", "maintenance-wizard"))
        if self.enabled:
            logger.info("LangSmith tracing enabled project=%s", self.project)
        else:
            logger.info("LangSmith tracing disabled; using local observability fallback")

    def record_event(self, name: str, payload: Dict[str, Any]) -> None:
        metrics.record(f"langsmith_{name}", float(payload.get("latency_ms", 0) or 0))
        if self.enabled:
            logger.info("LangSmith event=%s project=%s payload_keys=%s", name, self.project, sorted(payload.keys()))

    def health_status(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self.enabled else "local_fallback",
            "enabled": self.enabled,
            "project": self.project,
            "tracks": ["Workflow Execution", "Tool Calls", "Retrieval", "Agent Latency", "LLM Latency", "Failures"],
        }


langsmith_observer = LangSmithObserver()
