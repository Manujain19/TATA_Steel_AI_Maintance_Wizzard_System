from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, Iterable

from backend.telemetry.observability import metrics

logger = logging.getLogger(__name__)


class PreloadManager:
    """Runs heavyweight warmups after FastAPI is already available."""

    def __init__(self) -> None:
        self.running = False
        self.completed = False
        self.started_at: str | None = None
        self.completed_at: str | None = None
        self.error: str | None = None
        self.embedding_loaded = False
        self.reranker_loaded = False
        self.vector_store_loaded = False
        self.workflow_loaded = False
        self.dashboard_cache_loaded = False
        self.asset_cache_loaded = False
        self.kpi_cache_loaded = False
        self.latencies_ms: Dict[str, float] = {}
        self.failed_jobs: Dict[str, str] = {}
        self._task: asyncio.Task | None = None

    def launch(self, jobs: Dict[str, Callable[[], Any]]) -> None:
        if self._task and not self._task.done():
            return
        self.running = True
        self.completed = False
        self.started_at = datetime.now().isoformat(timespec="seconds")
        self.completed_at = None
        self.error = None
        self.failed_jobs = {}
        self._task = asyncio.create_task(self._run(jobs))

    async def _run(self, jobs: Dict[str, Callable[[], Any]]) -> None:
        started = time.perf_counter()
        try:
            await asyncio.gather(*(self._run_job(name, job) for name, job in jobs.items()))
            self.completed = not self.failed_jobs
            self.error = None if self.completed else "; ".join(f"{name}: {error}" for name, error in self.failed_jobs.items())
        except Exception as exc:
            self.completed = False
            self.error = str(exc)
            logger.warning("Preload manager failed: %s", exc)
        finally:
            self.running = False
            self.completed_at = datetime.now().isoformat(timespec="seconds")
            metrics.record("background_preload_total", (time.perf_counter() - started) * 1000)

    async def _run_job(self, name: str, job: Callable[[], Any]) -> None:
        started = time.perf_counter()
        try:
            await asyncio.to_thread(job)
            latency = round((time.perf_counter() - started) * 1000, 2)
            self.latencies_ms[name] = latency
            metrics.record(f"preload_{name}", latency)
            self._mark_loaded(name)
            logger.info("Preload job completed name=%s latency_ms=%s", name, latency)
        except Exception as exc:
            latency = round((time.perf_counter() - started) * 1000, 2)
            self.latencies_ms[name] = latency
            self.failed_jobs[name] = str(exc)
            logger.warning("Preload job skipped name=%s latency_ms=%s error=%s", name, latency, exc)

    def _mark_loaded(self, name: str) -> None:
        if "embedding" in name:
            self.embedding_loaded = True
        if "reranker" in name:
            self.reranker_loaded = True
        if "vector" in name or "chroma" in name:
            self.vector_store_loaded = True
        if "workflow" in name or "langgraph" in name:
            self.workflow_loaded = True
        if "dashboard" in name:
            self.dashboard_cache_loaded = True
        if "asset" in name:
            self.asset_cache_loaded = True
        if "kpi" in name:
            self.kpi_cache_loaded = True

    def status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "completed": self.completed,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "embedding_loaded": self.embedding_loaded,
            "reranker_loaded": self.reranker_loaded,
            "vector_store_loaded": self.vector_store_loaded,
            "workflow_loaded": self.workflow_loaded,
            "dashboard_cache_loaded": self.dashboard_cache_loaded,
            "asset_cache_loaded": self.asset_cache_loaded,
            "kpi_cache_loaded": self.kpi_cache_loaded,
            "latencies_ms": self.latencies_ms,
            "failed_jobs": self.failed_jobs,
        }
