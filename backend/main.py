from __future__ import annotations

import json
import logging
import asyncio
import importlib
import os
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "src"))

try:
    from fastapi import FastAPI, WebSocket
    from fastapi import HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
    from fastapi.staticfiles import StaticFiles
except Exception as exc:  # pragma: no cover
    raise RuntimeError("FastAPI backend requires fastapi and uvicorn. Install requirements.txt.") from exc

from backend.caches import LangGraphWorkflowCache, RAGPipelineCache
from backend.config import DATA_DIR, OUTPUT_DIR, ROOT_DIR, settings
from backend.db.postgres import initialize_schema, seed_from_json
from backend.models.schemas import CopilotRequest, ReportRequest, SearchRequest
from backend.services.data_repository import DataRepository
from backend.services.preload_manager import PreloadManager
from backend.telemetry.langsmith import langsmith_observer
from backend.telemetry.observability import metrics

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
for noisy_logger in [
    "httpx",
    "httpcore",
    "huggingface_hub",
    "huggingface_hub.utils._http",
    "sentence_transformers",
    "transformers",
    "urllib3",
]:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
PROCESS_STARTED_AT = time.perf_counter()
CONFIG_LOAD_MS = round((time.perf_counter() - PROCESS_STARTED_AT) * 1000, 2)
STARTUP_DURATION_MS = 0.0
ROUTE_REGISTRATION_MS = 0.0
BACKGROUND_STATUS = {
    "running": False,
    "completed": False,
    "started_at": None,
    "completed_at": None,
    "error": None,
}
MODEL_WARMUP_STATUS = {
    "launched": False,
    "running": False,
    "started_at": None,
    "completed_at": None,
    "embedding_warming": False,
    "reranker_warming": False,
    "embedding_loaded": False,
    "reranker_loaded": False,
    "embedding_error": None,
    "reranker_error": None,
    "embedding_breakdown": {},
    "reranker_breakdown": {},
    "embedding_fallback_active": False,
    "reranker_fallback_active": False,
    "embedding_fallback_reason": None,
    "reranker_fallback_reason": None,
    "embedding_real_model_loaded": False,
    "reranker_real_model_loaded": False,
    "latencies_ms": {},
}
MODEL_WARMUP_LOCK = threading.Lock()


class LazySingletonProxy:
    def __init__(self, name: str, factory: Callable):
        self.name = name
        self.factory = factory
        self._instance = None
        self._lock = threading.Lock()
        self.loaded = False
        self.loaded_at_ms = None

    def get(self):
        if self._instance is None:
            with self._lock:
                if self._instance is None:
                    started = time.perf_counter()
                    self._instance = self.factory()
                    self.loaded = True
                    self.loaded_at_ms = round((time.perf_counter() - started) * 1000, 2)
                    logger.info("Lazy singleton loaded name=%s load_ms=%s", self.name, self.loaded_at_ms)
        return self._instance

    def __getattr__(self, item):
        return getattr(self.get(), item)


class LazyFunction:
    def __init__(self, module_name: str, function_name: str) -> None:
        self.module_name = module_name
        self.function_name = function_name
        self._function = None
        self._lock = threading.Lock()

    def _load(self):
        if self._function is None:
            with self._lock:
                if self._function is None:
                    started = time.perf_counter()
                    module = importlib.import_module(self.module_name)
                    self._function = getattr(module, self.function_name)
                    logger.info(
                        "Lazy route helper loaded module=%s function=%s load_ms=%s",
                        self.module_name,
                        self.function_name,
                        round((time.perf_counter() - started) * 1000, 2),
                    )
        return self._function

    def __call__(self, *args, **kwargs):
        return self._load()(*args, **kwargs)


class TtlCache:
    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self.rows: dict[str, dict] = {}
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get_or_set(self, key: str, factory: Callable):
        now = time.time()
        with self.lock:
            row = self.rows.get(key)
            if row and now - row["created_at"] <= self.ttl_seconds:
                self.hits += 1
                return row["value"]
            self.misses += 1
        value = factory()
        with self.lock:
            self.rows[key] = {"created_at": now, "value": value}
        return value

    def get(self, key: str):
        now = time.time()
        with self.lock:
            row = self.rows.get(key)
            if row and now - row["created_at"] <= self.ttl_seconds:
                self.hits += 1
                return row["value"]
            self.misses += 1
            if row:
                self.rows.pop(key, None)
        return None

    def set(self, key: str, value):
        with self.lock:
            self.rows[key] = {"created_at": time.time(), "value": value}

    def status(self) -> dict:
        total = self.hits + self.misses
        return {
            "ttl_seconds": self.ttl_seconds,
            "entries": len(self.rows),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total, 4) if total else 0,
        }


def safe_dashboard_payload(name: str, factory: Callable, fallback: Callable):
    try:
        return dashboard_cache.get_or_set(name, factory)
    except Exception as exc:
        logger.exception("Dashboard payload generation failed name=%s error=%s", name, exc)
        return fallback()


def fallback_bootstrap() -> dict:
    assets = repo.assets()
    sensors = repo.sensors()
    spares = repo.spare_parts()
    failures = repo.failure_reports()
    return {
        "equipment": sensors,
        "spares": spares,
        "history": failures,
        "demo_queries": [],
        "alerts": [],
        "role_definitions": [],
        "role_notifications": [],
        "live_monitor": {"metrics": []},
        "intelligence": {},
        "knowledge_center": {},
        "agent_metrics": {},
        "enterprise": {},
        "brand": {"name": settings.app_name, "subtitle": "AI-Powered Industrial Reliability & Maintenance Intelligence"},
        "equipment_master": assets,
        "operations_center": {"kpis": [], "top_risks": []},
        "plant_command_center": {"kpis": [], "critical_assets": []},
        "plant_digital_twin": {"zones": [], "assets": assets},
        "ai_pipeline": {"steps": []},
        "report_catalog": [],
        "dependency_graph": {"nodes": [], "edges": []},
        "fallback": True,
        "status": "degraded",
    }


def fallback_dashboard(name: str) -> dict:
    return {"status": "degraded", "fallback": True, "name": name, "kpis": [], "items": []}


app = FastAPI(title=settings.app_name, version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def no_cache_frontend_assets(request, call_next):
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

repo = DataRepository()
rag = LazySingletonProxy("rag_pipeline", RAGPipelineCache.get)
workflow = LazySingletonProxy("langgraph_workflow", LangGraphWorkflowCache.get)
preload_manager = PreloadManager()
dashboard_cache = TtlCache(ttl_seconds=30 * 60)
asset_context_cache = TtlCache(ttl_seconds=15 * 60)
investigation_cache = TtlCache(ttl_seconds=10 * 60)

append_digital_log = LazyFunction("src.maintenance_wizard", "append_digital_log")
append_feedback = LazyFunction("src.maintenance_wizard", "append_feedback")
create_report_from_sources = LazyFunction("src.maintenance_wizard", "create_report_from_sources")
load_sources = LazyFunction("src.maintenance_wizard", "load_sources")
retrieve_context = LazyFunction("src.maintenance_wizard", "retrieve_context")
run_demo = LazyFunction("src.maintenance_wizard", "run_demo")
write_alert_report = LazyFunction("src.maintenance_wizard", "write_alert_report")
write_markdown_report = LazyFunction("src.maintenance_wizard", "write_markdown_report")

append_audit = LazyFunction("src.web_app", "append_audit")
build_ai_pipeline_visibility = LazyFunction("src.web_app", "build_ai_pipeline_visibility")
build_alerts = LazyFunction("src.web_app", "build_alerts")
build_alerts_from_sources = LazyFunction("src.web_app", "build_alerts_from_sources")
build_asset_context = LazyFunction("src.web_app", "build_asset_context")
build_bootstrap = LazyFunction("src.web_app", "build_bootstrap")
build_chat_response = LazyFunction("src.web_app", "build_chat_response")
build_dependency_graph = LazyFunction("src.web_app", "build_dependency_graph")
build_enterprise_dashboard = LazyFunction("src.web_app", "build_enterprise_dashboard")
build_enterprise_report = LazyFunction("src.web_app", "build_enterprise_report")
build_executive_report_pdf_text = LazyFunction("src.web_app", "build_executive_report_pdf_text")
build_failure_cost_impact = LazyFunction("src.web_app", "build_failure_cost_impact")
build_intelligence = LazyFunction("src.web_app", "build_intelligence")
build_incident_replay = LazyFunction("src.web_app", "build_incident_replay")
build_knowledge_sources = LazyFunction("src.web_app", "build_knowledge_sources")
build_live_monitor = LazyFunction("src.web_app", "build_live_monitor")
build_operations_center = LazyFunction("src.web_app", "build_operations_center")
build_plant_command_center = LazyFunction("src.web_app", "build_plant_command_center")
build_plant_digital_twin = LazyFunction("src.web_app", "build_plant_digital_twin")
build_role_notifications = LazyFunction("src.web_app", "build_role_notifications")
build_shift_handover_pdf_text = LazyFunction("src.web_app", "build_shift_handover_pdf_text")
build_work_order = LazyFunction("src.web_app", "build_work_order")
build_work_order_pdf_text = LazyFunction("src.web_app", "build_work_order_pdf_text")
make_simple_pdf = LazyFunction("src.web_app", "make_simple_pdf")
simulate_operation_strategy = LazyFunction("src.web_app", "simulate_operation_strategy")


def active_alert_code(equipment_id: str | None) -> str:
    if not equipment_id:
        return "unknown"
    for sensor in repo.sensors():
        if sensor.get("equipment_id") == equipment_id:
            return str(sensor.get("anomaly_alert") or sensor.get("active_alert") or "unknown")
    for asset in repo.assets():
        if asset.get("id") == equipment_id or asset.get("equipment_id") == equipment_id:
            return str(asset.get("active_alert") or asset.get("status") or "unknown")
    return "unknown"


def investigation_cache_key(equipment_id: str | None) -> str:
    return f"{equipment_id or 'auto'}:{active_alert_code(equipment_id)}"


def build_agentic_payload(state: dict) -> dict:
    report = state["report"]
    retrieved = state.get("retrieval", {}).get("documents", [])
    breaches = report["diagnosis"].get("condition_breaches", [])
    causes = report["diagnosis"].get("probable_root_causes", [])
    retrieval_score = min(100, round(sum(float(item.get("score", 0) or 0) for item in retrieved) * 18))
    history_score = min(100, 35 + len([item for item in retrieved if item.get("metadata", {}).get("source") == "failure_reports"]) * 12)
    anomaly_score = min(100, len(breaches) * 25)
    llm_confidence = round(float(state.get("llm_output", {}).get("llm_confidence_estimate", 0.82)) * 100)
    confidence = round(retrieval_score * 0.25 + history_score * 0.25 + anomaly_score * 0.30 + llm_confidence * 0.20)
    hybrid_stats = state.get("retrieval", {}).get("hybrid_retrieval", {})
    trace = state.get("execution_trace", [])
    execution = build_frontend_execution_trace(trace)
    retrieved_context = [
        f"{item.get('metadata', {}).get('source', 'knowledge')}: {item.get('metadata', {}).get('parent_id', item.get('id', 'document'))}"
        for item in retrieved[:6]
    ]
    reasoning = [
        f"Selected asset {report['equipment']['equipment_id']} has active alert {report['equipment']['active_alert']}.",
        f"Probable fault {report['diagnosis']['probable_fault']} is supported by sensor anomalies and retrieved maintenance history.",
        f"Risk score {report['risk']['score']} reflects condition severity, historical failures, and spare constraints.",
    ]
    observed = [
        f"{item['metric']} = {item['value']} breached {item['level']} limit {item['limit']}"
        for item in breaches
    ]
    return {
        "base_report": report,
        "agent_execution": execution,
        "reasoning_trace": {
            "observed_evidence": observed,
            "retrieved_context": retrieved_context,
            "reasoning": reasoning,
            "diagnosis_confidence": confidence,
            "reasoning_strength": "High" if confidence >= 85 else "Medium" if confidence >= 70 else "Low",
            "source_citations": build_source_citations(retrieved),
        },
        "llm_output": state.get("llm_output", {}),
        "ai_confidence": {
            "score": confidence,
            "retrieval_relevance": retrieval_score,
            "historical_match_rate": history_score,
            "sensor_anomaly_severity": anomaly_score,
            "llm_confidence_estimate": llm_confidence,
            "hybrid_retrieval_score": hybrid_stats.get("hybrid_retrieval_score", 0),
            "document_count": len(retrieved),
            "reasoning_strength": "High" if confidence >= 85 else "Medium" if confidence >= 70 else "Low",
        },
        "executive_ai_summary": state.get("final_response") or state.get("executive_summary") or report["recommendations"][0],
        "agent_metrics": {
            "agent_success_rate": 100 if execution else 0,
            "average_diagnosis_confidence": confidence,
            "knowledge_retrieval_accuracy": retrieval_score,
            "work_orders_generated": 1,
            "historical_match_rate": history_score,
        },
        "agent_work_order_fields": {},
        "workflow_engine": state.get("workflow_engine"),
        "workflow_status": state.get("workflow_status"),
        "llm_provider": "Maintenance Wizard Intelligence Engine",
        "root_causes": causes,
        "tool_results": state.get("tool_results", {}),
        "hybrid_retrieval": hybrid_stats,
    }


def build_frontend_execution_trace(trace: list[dict]) -> list[dict]:
    by_node = {item.get("node"): item for item in trace}
    sequence = [
        ("Sensor Analysis Completed", by_node.get("retriever_agent")),
        ("Asset Context Completed", by_node.get("retriever_agent")),
        ("Historical Failure Review Completed", by_node.get("retriever_agent")),
        ("Root Cause Analysis Completed", by_node.get("root_cause_agent")),
        ("Risk Assessment Completed", by_node.get("diagnosis_agent")),
        ("Spare Parts Review Completed", by_node.get("inventory_agent")),
        ("Maintenance Plan Generated", by_node.get("maintenance_planner_agent")),
        ("Work Order Generated", by_node.get("response_node")),
    ]
    fallback_time = datetime.now().isoformat(timespec="seconds")
    return [
        {
            **(source or {}),
            "agent_name": label,
            "started_at": (source or {}).get("started_at", fallback_time),
            "completed_at": (source or {}).get("completed_at", fallback_time),
            "status": (source or {}).get("status", "success"),
            "progress": (source or {}).get("progress", 100),
            "steps": (source or {}).get("steps", [label]),
        }
        for label, source in sequence
    ]


def build_source_citations(documents: list[dict]) -> dict:
    citations = {
        "manual_references": [],
        "sop_references": [],
        "failure_report_references": [],
        "maintenance_log_references": [],
    }
    for item in documents:
        metadata = item.get("metadata", {})
        source = str(metadata.get("source", ""))
        reference = str(metadata.get("parent_id") or item.get("id") or "document")
        if "manual" in source:
            citations["manual_references"].append(reference)
        elif "sop" in source:
            citations["sop_references"].append(reference)
        elif "failure" in source:
            citations["failure_report_references"].append(reference)
        elif "maintenance" in source:
            citations["maintenance_log_references"].append(reference)
    return {key: sorted(set(value))[:5] for key, value in citations.items()}


@app.on_event("startup")
async def startup() -> None:
    global STARTUP_DURATION_MS, ROUTE_REGISTRATION_MS

    startup_started = time.perf_counter()
    route_started = time.perf_counter()

    ROUTE_REGISTRATION_MS = round((route_started - PROCESS_STARTED_AT) * 1000, 2)

    logger.warning(
        "DEBUG BACKGROUND_PRELOAD_AI_MODELS=%s",
        settings.background_preload_ai_models,
    )

    logger.warning(
        "DEBUG EAGER_LOAD_AI_MODELS=%s",
        settings.eager_load_ai_models,
    )

    logger.warning(
        "DEBUG ENABLE_RUNTIME_MODEL_LOADING=%s",
        settings.enable_runtime_model_loading,
    )

    logger.warning(
        "DEBUG ALLOW_MODEL_FALLBACK=%s",
        settings.allow_model_fallback,
    )

    if settings.llm_fail_fast:
        logger.warning(
            "LLM_FAIL_FAST is deferred to preload to keep FastAPI startup non-blocking."
        )

    preload_launch_started = time.perf_counter()
    ensure_preload_started("startup")
    launch_post_ready_model_warmup_watcher()
    preload_launch_ms = round((time.perf_counter() - preload_launch_started) * 1000, 2)
    STARTUP_DURATION_MS = round((time.perf_counter() - startup_started) * 1000, 2)
    metrics.record("config_load_ms", CONFIG_LOAD_MS)
    metrics.record("route_registration_ms", ROUTE_REGISTRATION_MS)
    metrics.record("background_preload_launch_ms", preload_launch_ms)
    metrics.record("startup_ms", STARTUP_DURATION_MS)
    logger.info(
        "Startup profile config_load_ms=%s route_registration_ms=%s workflow_registration_ms=%s background_preload_launch_ms=%s startup_ms=%s",
        CONFIG_LOAD_MS,
        ROUTE_REGISTRATION_MS,
        0,
        preload_launch_ms,
        STARTUP_DURATION_MS,
    )


def build_preload_jobs() -> dict[str, Callable]:
    _update_model_warmup_status(
        launched=False,
        running=False,
        started_at=None,
        completed_at=None,
        embedding_warming=False,
        reranker_warming=False,
        embedding_error=None,
        reranker_error=None,
        embedding_fallback_active=False,
        reranker_fallback_active=False,
        embedding_fallback_reason=None,
        reranker_fallback_reason=None,
        embedding_real_model_loaded=False,
        reranker_real_model_loaded=False,
    )

    def postgres_seed() -> None:
        initialize_schema()
        seed_from_json(repo)

    def warm_vector() -> None:
        started = time.perf_counter()
        current_rag = rag.get()
        deadline = time.time() + 30
        last_status = {}
        while time.time() < deadline:
            current_rag.ensure_index()
            store = current_rag.vector_store
            ready = store.is_ready() if hasattr(store, "is_ready") else False
            status = store.status()
            last_status = status
            logger.info(
                "Vector warmup status EXPECTED_COLLECTION=%s ACTUAL_COLLECTION=%s PERSIST_DIRECTORY=%s backend=%s document_count=%s ready=%s",
                status.get("expected_collection", "maintenance_knowledge_d384"),
                status.get("collection"),
                status.get("persist_directory"),
                status.get("backend"),
                status.get("document_count"),
                ready,
            )
            if ready:
                metrics.record("startup_vectorstore_ms", (time.perf_counter() - started) * 1000)
                return
            time.sleep(0.75)
        raise RuntimeError(
            f"ChromaDB vector store not ready backend={last_status.get('backend')} "
            f"collection={last_status.get('collection')} document_count={last_status.get('document_count')} "
            f"persist_directory={last_status.get('persist_directory')} error={last_status.get('initialization_error')}"
        )

    def warm_workflow() -> None:
        started = time.perf_counter()
        status = workflow.get().health_status()
        if not status:
            raise RuntimeError("Workflow health status unavailable")
        metrics.record("startup_workflow_ms", (time.perf_counter() - started) * 1000)

    def warm_embedding() -> None:
        with MODEL_WARMUP_LOCK:
            MODEL_WARMUP_STATUS.update(
                {
                    "launched": True,
                    "running": True,
                    "started_at": MODEL_WARMUP_STATUS["started_at"] or datetime.now().isoformat(timespec="seconds"),
                    "embedding_warming": True,
                    "embedding_error": None,
                }
            )
        started = time.perf_counter()
        try:
            current_rag = rag.get()
            status = current_rag.embedding_service.warmup()
            latency = round((time.perf_counter() - started) * 1000, 2)
            with MODEL_WARMUP_LOCK:
                MODEL_WARMUP_STATUS["latencies_ms"]["embedding_warmup"] = latency
                MODEL_WARMUP_STATUS["latencies_ms"]["startup_embedding_ms"] = status.get("latency_ms", latency)
                MODEL_WARMUP_STATUS["embedding_breakdown"] = status.get("timing_breakdown", {})
                MODEL_WARMUP_STATUS.update(
                    {
                        "embedding_loaded": True,
                        "embedding_warming": False,
                        "embedding_fallback_active": bool(status.get("fallback_active")),
                        "embedding_fallback_reason": status.get("fallback_reason"),
                        "embedding_real_model_loaded": bool(status.get("real_model_loaded")),
                        "embedding_error": None,
                    }
                )
            if status.get("fallback_active"):
                logger.warning("Startup embedding warmup using fallback reason=%s", status.get("fallback_reason"))
            logger.info("Startup embedding warmup completed model=%s latency_ms=%s", status.get("model"), latency)
        except Exception as exc:
            latency = round((time.perf_counter() - started) * 1000, 2)
            with MODEL_WARMUP_LOCK:
                MODEL_WARMUP_STATUS["latencies_ms"]["embedding_warmup"] = latency
                MODEL_WARMUP_STATUS.update({"embedding_loaded": False, "embedding_warming": False, "embedding_error": str(exc)})
            raise
        finally:
            _finalize_model_warmup_if_done()

    def warm_reranker() -> None:
        with MODEL_WARMUP_LOCK:
            MODEL_WARMUP_STATUS.update(
                {
                    "launched": True,
                    "running": True,
                    "started_at": MODEL_WARMUP_STATUS["started_at"] or datetime.now().isoformat(timespec="seconds"),
                    "reranker_warming": True,
                    "reranker_error": None,
                }
            )
        started = time.perf_counter()
        try:
            current_rag = rag.get()
            status = current_rag.reranker.warmup()
            latency = round((time.perf_counter() - started) * 1000, 2)
            with MODEL_WARMUP_LOCK:
                MODEL_WARMUP_STATUS["latencies_ms"]["reranker_warmup"] = latency
                MODEL_WARMUP_STATUS["latencies_ms"]["startup_reranker_ms"] = status.get("latency_ms", latency)
                MODEL_WARMUP_STATUS["reranker_breakdown"] = status.get("timing_breakdown", {})
                MODEL_WARMUP_STATUS.update(
                    {
                        "reranker_loaded": True,
                        "reranker_warming": False,
                        "reranker_fallback_active": bool(status.get("fallback_active")),
                        "reranker_fallback_reason": status.get("fallback_reason"),
                        "reranker_real_model_loaded": bool(status.get("real_model_loaded")),
                        "reranker_error": None,
                    }
                )
            if status.get("fallback_active"):
                logger.warning("Startup reranker warmup using fallback reason=%s", status.get("fallback_reason"))
            logger.info("Startup reranker warmup completed model=%s latency_ms=%s", status.get("model"), latency)
        except Exception as exc:
            latency = round((time.perf_counter() - started) * 1000, 2)
            with MODEL_WARMUP_LOCK:
                MODEL_WARMUP_STATUS["latencies_ms"]["reranker_warmup"] = latency
                MODEL_WARMUP_STATUS.update({"reranker_loaded": False, "reranker_warming": False, "reranker_error": str(exc)})
            raise
        finally:
            _finalize_model_warmup_if_done()

    def warm_dashboards() -> None:
        for key, factory in {
            "bootstrap": build_bootstrap,
            "operations_center": build_operations_center,
            "plant_command_center": build_plant_command_center,
            "digital_twin": build_plant_digital_twin,
            "enterprise": build_enterprise_dashboard,
            "intelligence": build_intelligence,
        }.items():
            value = factory()
            if value is None:
                raise RuntimeError(f"Dashboard cache warmup returned empty payload key={key}")
            dashboard_cache.set(key, value)

    def warm_assets() -> None:
        for asset in repo.assets():
            equipment_id = asset.get("id") or asset.get("equipment_id")
            if equipment_id:
                value = build_asset_context(str(equipment_id))
                if not value or value.get("fallback"):
                    raise RuntimeError(f"Asset context warmup failed equipment_id={equipment_id}")
                asset_context_cache.set(str(equipment_id), value)

    def warm_kpis() -> None:
        dashboard_cache.get_or_set("plant_command_center", build_plant_command_center)
        dashboard_cache.get_or_set("operations_center", build_operations_center)

    return {
        "postgres_seed": postgres_seed,
        "vector_store_warmup": warm_vector,
        "workflow_compile": warm_workflow,

        "embedding_model_warmup": warm_embedding,
        "reranker_model_warmup": warm_reranker,

        "dashboard_cache_warmup": warm_dashboards,
        "asset_cache_warmup": warm_assets,
        "kpi_cache_warmup": warm_kpis,
    }


def ensure_preload_started(reason: str = "startup") -> bool:
    if not settings.background_preload_ai_models:
        logger.warning("Preload launch skipped reason=%s background_preload=false", reason)
        return False
    if preload_manager.running or preload_manager.completed or preload_manager.started_at:
        return False
    BACKGROUND_STATUS.update(
        {
            "running": True,
            "completed": False,
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "completed_at": None,
            "error": None,
        }
    )
    jobs = build_preload_jobs()
    logger.warning("PRELOAD JOBS FOUND=%s reason=%s", list(jobs.keys()), reason)
    preload_manager.launch(jobs)
    logger.warning("PRELOAD MANAGER STARTED reason=%s", reason)
    return True


def model_warmup_status() -> dict:
    with MODEL_WARMUP_LOCK:
        return {
            **MODEL_WARMUP_STATUS,
            "latencies_ms": dict(MODEL_WARMUP_STATUS.get("latencies_ms", {})),
        }


def _update_model_warmup_status(**updates) -> None:
    with MODEL_WARMUP_LOCK:
        MODEL_WARMUP_STATUS.update(updates)


def _finalize_model_warmup_if_done() -> None:
    with MODEL_WARMUP_LOCK:
        if MODEL_WARMUP_STATUS["embedding_warming"] or MODEL_WARMUP_STATUS["reranker_warming"]:
            return
        if not (MODEL_WARMUP_STATUS["embedding_loaded"] or MODEL_WARMUP_STATUS["reranker_loaded"]):
            return
        MODEL_WARMUP_STATUS.update(
            {
                "running": False,
                "completed_at": datetime.now().isoformat(timespec="seconds"),
            }
        )


def _core_runtime_ready() -> bool:
    rag_loaded = bool(getattr(rag, "loaded", False))
    workflow_loaded = bool(getattr(workflow, "loaded", False))
    current_rag = rag._instance if rag_loaded else None
    vector_ready = bool(
        current_rag
        and current_rag.vector_store
        and getattr(current_rag.vector_store, "is_ready", lambda: False)()
    )
    return bool(vector_ready and workflow_loaded)


def _warm_embedding_model(current_rag) -> None:
    if current_rag.embedding_service.model is not None:
        _update_model_warmup_status(embedding_loaded=True, embedding_real_model_loaded=True, embedding_warming=False)
        return
    started = time.perf_counter()
    _update_model_warmup_status(embedding_warming=True, embedding_error=None)
    try:
        status = current_rag.embedding_service.warmup()
        loaded = bool(status.get("real_model_loaded") or (settings.allow_model_fallback and status.get("fallback_active")))
        latency = round((time.perf_counter() - started) * 1000, 2)
        with MODEL_WARMUP_LOCK:
            MODEL_WARMUP_STATUS["latencies_ms"]["embedding_warmup"] = latency
            MODEL_WARMUP_STATUS["latencies_ms"]["startup_embedding_ms"] = status.get("latency_ms", latency)
            MODEL_WARMUP_STATUS["embedding_breakdown"] = status.get("timing_breakdown", {})
            MODEL_WARMUP_STATUS.update(
                {
                    "embedding_loaded": loaded,
                    "embedding_warming": False,
                    "embedding_fallback_active": bool(status.get("fallback_active")),
                    "embedding_fallback_reason": status.get("fallback_reason"),
                    "embedding_real_model_loaded": bool(status.get("real_model_loaded")),
                    "embedding_error": None if loaded else status.get("fallback_reason") or f"Embedding model unavailable backend={current_rag.embedding_service.backend}",
                }
            )
        metrics.record("post_ready_embedding_warmup", latency)
    except Exception as exc:
        latency = round((time.perf_counter() - started) * 1000, 2)
        with MODEL_WARMUP_LOCK:
            MODEL_WARMUP_STATUS["latencies_ms"]["embedding_warmup"] = latency
            MODEL_WARMUP_STATUS.update({"embedding_warming": False, "embedding_loaded": False, "embedding_error": str(exc)})
        logger.warning("Post-ready embedding warmup failed latency_ms=%s error=%s", latency, exc)


def _warm_reranker_model(current_rag) -> None:
    if current_rag.reranker.model is not None:
        _update_model_warmup_status(reranker_loaded=True, reranker_real_model_loaded=True, reranker_warming=False)
        return
    started = time.perf_counter()
    _update_model_warmup_status(reranker_warming=True, reranker_error=None)
    try:
        status = current_rag.reranker.warmup()
        loaded = bool(status.get("real_model_loaded") or (settings.allow_model_fallback and status.get("fallback_active")))
        latency = round((time.perf_counter() - started) * 1000, 2)
        with MODEL_WARMUP_LOCK:
            MODEL_WARMUP_STATUS["latencies_ms"]["reranker_warmup"] = latency
            MODEL_WARMUP_STATUS["latencies_ms"]["startup_reranker_ms"] = status.get("latency_ms", latency)
            MODEL_WARMUP_STATUS["reranker_breakdown"] = status.get("timing_breakdown", {})
            MODEL_WARMUP_STATUS.update(
                {
                    "reranker_loaded": loaded,
                    "reranker_warming": False,
                    "reranker_fallback_active": bool(status.get("fallback_active")),
                    "reranker_fallback_reason": status.get("fallback_reason"),
                    "reranker_real_model_loaded": bool(status.get("real_model_loaded")),
                    "reranker_error": None if loaded else status.get("fallback_reason") or f"Reranker model unavailable backend={current_rag.reranker.backend}",
                }
            )
        metrics.record("post_ready_reranker_warmup", latency)
    except Exception as exc:
        latency = round((time.perf_counter() - started) * 1000, 2)
        with MODEL_WARMUP_LOCK:
            MODEL_WARMUP_STATUS["latencies_ms"]["reranker_warmup"] = latency
            MODEL_WARMUP_STATUS.update({"reranker_warming": False, "reranker_loaded": False, "reranker_error": str(exc)})
        logger.warning("Post-ready reranker warmup failed latency_ms=%s error=%s", latency, exc)


def _run_post_ready_model_warmup() -> None:
    with MODEL_WARMUP_LOCK:
        if MODEL_WARMUP_STATUS["running"] or (
            MODEL_WARMUP_STATUS["embedding_loaded"] and MODEL_WARMUP_STATUS["reranker_loaded"]
        ):
            return
        MODEL_WARMUP_STATUS.update(
            {
                "launched": True,
                "running": True,
                "started_at": datetime.now().isoformat(timespec="seconds"),
                "completed_at": None,
                "embedding_warming": True,
                "reranker_warming": True,
                "embedding_error": None,
                "reranker_error": None,
            }
        )
    logger.info("Post-ready AI model warmup started")
    started = time.perf_counter()
    try:
        current_rag = rag.get()
        threads = [
            threading.Thread(target=_warm_embedding_model, args=(current_rag,), name="embedding-model-warmup", daemon=True),
            threading.Thread(target=_warm_reranker_model, args=(current_rag,), name="reranker-model-warmup", daemon=True),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    finally:
        latency = round((time.perf_counter() - started) * 1000, 2)
        with MODEL_WARMUP_LOCK:
            MODEL_WARMUP_STATUS["latencies_ms"]["total_model_warmup"] = latency
            MODEL_WARMUP_STATUS.update(
                {
                    "running": False,
                    "embedding_warming": False,
                    "reranker_warming": False,
                    "completed_at": datetime.now().isoformat(timespec="seconds"),
                }
            )
        metrics.record("post_ready_model_warmup_total", latency)
        logger.info("Post-ready AI model warmup finished latency_ms=%s status=%s", latency, model_warmup_status())


def launch_post_ready_model_warmup_watcher() -> None:
    with MODEL_WARMUP_LOCK:
        if MODEL_WARMUP_STATUS["launched"]:
            return

    def watcher() -> None:
        deadline = time.time() + 180
        while time.time() < deadline:
            if _core_runtime_ready():
                _run_post_ready_model_warmup()
                return
            time.sleep(0.5)
        logger.warning("Post-ready AI model warmup watcher timed out waiting for core readiness")

    threading.Thread(target=watcher, name="post-ready-model-warmup-watcher", daemon=True).start()


def preload_status_payload() -> dict:
    ensure_preload_started("status_request")
    manager_status = preload_manager.status()
    warmup_status = model_warmup_status()
    BACKGROUND_STATUS.update(
        {
            "running": manager_status["running"],
            "completed": manager_status["completed"],
            "started_at": manager_status["started_at"],
            "completed_at": manager_status["completed_at"],
            "error": manager_status["error"],
        }
    )
    rag_loaded = bool(getattr(rag, "loaded", False))
    workflow_loaded = bool(getattr(workflow, "loaded", False))
    current_rag = rag._instance if rag_loaded else None
    vector_status = current_rag.vector_store.status() if current_rag and current_rag.vector_store else {}
    vector_ready = bool(current_rag and current_rag.vector_store and getattr(current_rag.vector_store, "is_ready", lambda: False)())
    embedding_loaded = bool(current_rag and current_rag.embedding_service.model)
    reranker_loaded = bool(current_rag and current_rag.reranker.model)
    if embedding_loaded and not warmup_status["embedding_loaded"]:
        warmup_status["embedding_loaded"] = True
        warmup_status["embedding_warming"] = False
        _update_model_warmup_status(embedding_loaded=True, embedding_warming=False)
    if reranker_loaded and not warmup_status["reranker_loaded"]:
        warmup_status["reranker_loaded"] = True
        warmup_status["reranker_warming"] = False
        _update_model_warmup_status(reranker_loaded=True, reranker_warming=False)
    payload = {
        **manager_status,
        "embedding_loaded": warmup_status["embedding_loaded"] or embedding_loaded,
        "reranker_loaded": warmup_status["reranker_loaded"] or reranker_loaded,
        "embedding_warming": warmup_status["embedding_warming"],
        "reranker_warming": warmup_status["reranker_warming"],
        "ai_model_ready": bool((warmup_status["embedding_loaded"] or embedding_loaded) and (warmup_status["reranker_loaded"] or reranker_loaded)),
        "model_warmup": warmup_status,
        "model_mode": settings.model_mode,
        "model_cache_directory": settings.model_cache_dir,
        "embedding_real_model_loaded": bool(warmup_status.get("embedding_real_model_loaded") or embedding_loaded),
        "reranker_real_model_loaded": bool(warmup_status.get("reranker_real_model_loaded") or reranker_loaded),
        "embedding_fallback_active": bool(warmup_status.get("embedding_fallback_active")),
        "reranker_fallback_active": bool(warmup_status.get("reranker_fallback_active")),
        "embedding_fallback_reason": warmup_status.get("embedding_fallback_reason"),
        "reranker_fallback_reason": warmup_status.get("reranker_fallback_reason"),
        "vector_store_loaded": vector_ready,
        "vector_store": vector_status,
        "workflow_loaded": manager_status["workflow_loaded"] or workflow_loaded,
    }
    core_ready = bool(payload["vector_store_loaded"] and payload["workflow_loaded"])
    payload["system_ready"] = core_ready
    payload["completed"] = bool(manager_status["completed"] or core_ready)
    payload["running"] = bool(manager_status["running"] and not core_ready)
    if core_ready and payload.get("failed_jobs"):
        payload["recovered_jobs"] = dict(payload["failed_jobs"])
        payload["failed_jobs"] = {}
        payload["error"] = None
    completed_steps = sum(
        1
        for key in ("vector_store_loaded", "workflow_loaded")
        if payload.get(key)
    )
    payload["ready_steps_completed"] = completed_steps
    payload["ready_steps_total"] = 2
    payload["ready_progress_percent"] = round(completed_steps / 2 * 100)
    payload["startup_embedding_ms"] = warmup_status.get("latencies_ms", {}).get("startup_embedding_ms") or manager_status.get("latencies_ms", {}).get("embedding_model_warmup")
    payload["startup_reranker_ms"] = warmup_status.get("latencies_ms", {}).get("startup_reranker_ms") or manager_status.get("latencies_ms", {}).get("reranker_model_warmup")
    payload["startup_vectorstore_ms"] = manager_status.get("latencies_ms", {}).get("vector_store_warmup")
    payload["startup_workflow_ms"] = manager_status.get("latencies_ms", {}).get("workflow_compile")
    payload["embedding_model_timing"] = warmup_status.get("embedding_breakdown", {})
    payload["reranker_model_timing"] = warmup_status.get("reranker_breakdown", {})
    payload["embedding_model_path"] = payload["embedding_model_timing"].get("embedding_model_path") or payload["embedding_model_timing"].get("model_path")
    payload["reranker_model_path"] = payload["reranker_model_timing"].get("reranker_model_path") or payload["reranker_model_timing"].get("model_path")
    payload["model_timing_breakdown"] = {
        "embedding": payload["embedding_model_timing"],
        "reranker": payload["reranker_model_timing"],
    }
    payload["fallback_active"] = bool(payload.get("embedding_fallback_active") or payload.get("reranker_fallback_active"))
    payload["retrieval_mode"] = retrieval_mode_from_status(payload)
    return payload


def system_ready() -> bool:
    status = preload_status_payload()
    return bool(status.get("system_ready"))


def ai_stack_ready() -> bool:
    status = preload_status_payload()
    return bool(status.get("system_ready") and status.get("ai_model_ready"))


def retrieval_mode_from_status(status: dict) -> str:
    embedding_real = bool(status.get("embedding_real_model_loaded"))
    reranker_real = bool(status.get("reranker_real_model_loaded"))
    if embedding_real and reranker_real:
        return "Hybrid RAG"
    if embedding_real:
        return "Semantic RAG"
    if status.get("fallback_active"):
        return "Lexical Fallback"
    if not status.get("embedding_loaded") and not status.get("reranker_loaded"):
        return "Semantic Retrieval Disabled"
    return "Initializing"


def require_ai_ready() -> None:
    if not ai_stack_ready():
        raise HTTPException(status_code=425, detail="AI stack is initializing. Please wait.")


def background_preload() -> None:
    started = time.perf_counter()
    logger.info("Background AI preload started")
    try:
        current_rag = rag.get()
        current_workflow = workflow.get()
        current_rag.ensure_index()
        try:
            build_bootstrap()
            build_plant_digital_twin()
            build_operations_center()
            build_plant_command_center()
        except Exception as analytics_exc:
            logger.warning("Background dashboard precompute skipped: %s", analytics_exc)
        current_workflow.health_status()
        metrics.record("background_preload_ai_models", (time.perf_counter() - started) * 1000)
        BACKGROUND_STATUS.update({"running": False, "completed": True, "completed_at": datetime.now().isoformat(timespec="seconds"), "error": None})
        logger.info("Background AI preload completed")
    except Exception as exc:
        BACKGROUND_STATUS.update({"running": False, "completed": False, "completed_at": datetime.now().isoformat(timespec="seconds"), "error": str(exc)})
        logger.warning("Background AI preload failed: %s", exc)


@app.get("/")
async def index():
    return FileResponse(
        ROOT_DIR / "web" / "index.html",
        media_type="text/html",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.head("/")
async def index_head():
    return Response(status_code=200)


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)


STATIC_DIR = ROOT_DIR / "web"
STATIC_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}
STATIC_MEDIA_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".mjs": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}


def static_file_path(asset_path: str) -> Path:
    candidate = (STATIC_DIR / asset_path).resolve()
    static_root = STATIC_DIR.resolve()
    if static_root != candidate and static_root not in candidate.parents:
        raise HTTPException(status_code=404, detail="Static asset not found")
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Static asset not found")
    return candidate


@app.get("/static/{asset_path:path}", include_in_schema=False)
async def static_asset(asset_path: str):
    file_path = static_file_path(asset_path)
    media_type = STATIC_MEDIA_TYPES.get(file_path.suffix.lower(), "application/octet-stream")
    return FileResponse(file_path, media_type=media_type, headers=STATIC_HEADERS)


@app.get("/api/static-health")
async def static_health():
    files = {}
    for name in ["index.html", "styles.css", "app.js", "digital_twin.js"]:
        path = STATIC_DIR / name
        files[name] = {
            "exists": path.is_file(),
            "size_bytes": path.stat().st_size if path.is_file() else 0,
            "path": str(path),
        }
    return {
        "healthy": all(item["exists"] and item["size_bytes"] > 0 for item in files.values()),
        "static_directory": str(STATIC_DIR),
        "files": files,
    }


app.mount("/static-files", StaticFiles(directory=STATIC_DIR), name="static-files")


@app.get("/api/bootstrap")
async def bootstrap():
    return safe_dashboard_payload("bootstrap", build_bootstrap, fallback_bootstrap)


@app.get("/api/assets")
async def assets():
    return {"assets": repo.assets()}


@app.get("/api/sensors")
async def sensors(equipment_id: Optional[str] = None):
    rows = repo.sensors()
    if equipment_id:
        rows = [item for item in rows if item.get("equipment_id") == equipment_id]
    return {"sensors": rows}


@app.get("/api/failures")
async def failures(equipment_id: Optional[str] = None):
    rows = repo.failure_reports()
    if equipment_id:
        rows = [item for item in rows if item.get("equipment_id") == equipment_id]
    return {"failures": rows}


@app.get("/api/workorders")
async def workorders(equipment_id: Optional[str] = None):
    rows = repo.work_orders()
    if equipment_id:
        rows = [item for item in rows if item.get("equipment_id") == equipment_id]
    return {"workorders": rows}


@app.post("/api/copilot")
async def copilot(payload: CopilotRequest):
    require_ai_ready()
    return workflow.run(payload.message, payload.equipment_id)


@app.post("/api/analyze")
async def analyze(payload: dict):
    require_ai_ready()
    query = str(payload.get("query", "")).strip()
    equipment_id = str(payload.get("equipment_id", "")).strip() or None
    feedback = str(payload.get("feedback", "")).strip() or None
    if not query:
        raise HTTPException(status_code=400, detail="Query is required.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Investigation request received route=/api/analyze equipment_id=%s", equipment_id)
    cache_key = investigation_cache_key(equipment_id)
    if not feedback:
        cached = investigation_cache.get(cache_key)
        if cached is not None:
            cached = {**cached, "cached_response_used": True}
            request_metrics = dict(cached.get("request_metrics") or {})
            request_metrics.update(
                {
                    "request_type": "investigation_cache",
                    "equipment_id": equipment_id,
                    "cached_response_used": True,
                }
            )
            metrics.record_request(**request_metrics)
            metrics.record("investigation_cache_hit", 1)
            return cached
    workflow_state = await workflow.run_investigation_async(query, equipment_id)
    report = workflow_state["report"]
    agentic = build_agentic_payload(workflow_state)
    sources = load_sources(DATA_DIR)
    work_order = build_work_order(report, sources)
    failure_cost_impact = build_failure_cost_impact(report)
    (OUTPUT_DIR / "maintenance_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "agentic_report.json").write_text(json.dumps(agentic, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "work_order.json").write_text(json.dumps(work_order, indent=2), encoding="utf-8")
    write_markdown_report(report, OUTPUT_DIR / "maintenance_report.md")
    write_alert_report(DATA_DIR, OUTPUT_DIR / "alert_report.csv")
    append_digital_log(OUTPUT_DIR, report)
    append_audit("maintenance_engineer", "analyzed equipment condition", report["equipment"]["equipment_id"], "ANALYZE")
    if feedback:
        append_feedback(OUTPUT_DIR, report["equipment"]["equipment_id"], feedback)
    logger.info(
        "Investigation workflow completed equipment_id=%s risk=%s workflow_engine=%s",
        report["equipment"]["equipment_id"],
        report["risk"]["level"],
        workflow_state.get("workflow_engine"),
    )
    request_metrics = {
        "request_type": "investigation",
        "equipment_id": report["equipment"]["equipment_id"],
        "workflow_engine": workflow_state.get("workflow_engine"),
        "retrieval_ms": workflow_state.get("retrieval_ms"),
        "rerank_ms": workflow_state.get("rerank_ms"),
        "llm_ms": workflow_state.get("llm_ms"),
        "workflow_ms": workflow_state.get("workflow_ms"),
        "total_request_ms": workflow_state.get("total_request_ms"),
        "cached_response_used": False,
    }
    payload = {
        "report": report,
        "agentic": agentic,
        "work_order": work_order,
        "failure_cost_impact": failure_cost_impact,
        "financial_impact": failure_cost_impact,
        "alerts": build_alerts(),
        "cached_response_used": False,
        "request_metrics": request_metrics,
    }
    if not feedback:
        investigation_cache.set(cache_key, payload)
    return payload


@app.post("/api/demo")
async def demo():
    reports = run_demo(DATA_DIR, OUTPUT_DIR)
    return {"reports": reports, "alerts": build_alerts()}


@app.post("/api/chat")
async def chat(payload: CopilotRequest):
    require_ai_ready()
    equipment_id = payload.equipment_id
    message = str(payload.message or "").strip()
    history = payload.history if isinstance(payload.history, list) else []
    if not message:
        raise HTTPException(status_code=400, detail="Message is required.")

    context_messages = [
        str(item.get("content", ""))
        for item in history[-4:]
        if isinstance(item, dict) and item.get("content")
    ]
    query = " ".join(context_messages + [message])
    lower_query = query.lower()
    complex_markers = [
        "investigation",
        "root cause",
        "rca",
        "executive report",
        "maintenance plan",
        "work order",
        "procurement",
        "shutdown",
    ]
    if any(marker in lower_query for marker in complex_markers):
        workflow_state = await workflow.run_investigation_async(query, equipment_id)
    else:
        workflow_state = workflow.run_lightweight(query, equipment_id)
    report = workflow_state["report"]
    response = workflow_state.get("final_response") or build_chat_response(report)
    agentic = build_agentic_payload(workflow_state)
    failure_cost_impact = build_failure_cost_impact(report)
    turn = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "equipment_id": report["equipment"]["equipment_id"],
        "user": message,
        "assistant": response,
        "message": response,
        "response": response,
        "content": response,
        "answer": response,
        "risk_level": report["risk"]["level"],
        "sources": agentic["reasoning_trace"].get("source_citations", {}),
        "confidence": agentic["ai_confidence"],
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUTPUT_DIR / "conversation_log.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(turn) + "\n")
    append_audit("maintenance_engineer", "asked copilot follow-up", report["equipment"]["equipment_id"], "CHAT")
    return {
        "turn": turn,
        "report": report,
        "agentic": agentic,
        "failure_cost_impact": failure_cost_impact,
        "financial_impact": failure_cost_impact,
        "timing": {
            "retrieval_ms": workflow_state.get("retrieval_ms"),
            "rerank_ms": workflow_state.get("rerank_ms"),
            "llm_ms": workflow_state.get("llm_ms"),
            "total_ms": workflow_state.get("total_request_ms") or workflow_state.get("workflow_ms"),
        },
        "message": response,
        "response": response,
        "content": response,
        "answer": response,
        "citations": agentic["reasoning_trace"].get("source_citations", {}),
        "confidence": round(agentic["ai_confidence"]["score"] / 100, 2),
    }


@app.get("/api/investigation-stream")
async def investigation_stream(equipment_id: Optional[str] = None, query: str = "Run investigation"):
    require_ai_ready()

    async def event_stream():
        started = time.perf_counter()
        for stage in ["Retrieving documents...", "Running RCA...", "Checking inventory...", "Generating report..."]:
            payload = {
                "stage": stage,
                "status": "running",
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            }
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(0)
        workflow_state = workflow.run(query, equipment_id)
        report = workflow_state.get("report", {})
        final_payload = {
            "stage": "Complete",
            "status": "completed",
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "equipment_id": report.get("equipment", {}).get("equipment_id"),
            "risk_level": report.get("risk", {}).get("level"),
        }
        yield f"data: {json.dumps(final_payload)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/rul")
async def rul(equipment_id: str):
    context = build_asset_context(equipment_id)
    return context["asset_intelligence"]["rul_model"]


@app.get("/api/business-impact")
async def business_impact(equipment_id: str):
    return build_asset_context(equipment_id)["failure_cost_impact"]


@app.get("/api/live")
async def live():
    return safe_dashboard_payload("live_monitor", build_live_monitor, lambda: fallback_dashboard("live_monitor"))


@app.get("/api/intelligence")
async def intelligence():
    return safe_dashboard_payload("intelligence", build_intelligence, lambda: fallback_dashboard("intelligence"))


@app.get("/api/knowledge-center")
async def knowledge_center():
    return build_knowledge_sources()


@app.get("/api/enterprise")
async def enterprise():
    return safe_dashboard_payload("enterprise", build_enterprise_dashboard, lambda: fallback_dashboard("enterprise"))


@app.get("/api/incident-replay")
async def incident_replay(equipment_id: Optional[str] = None):
    try:
        if equipment_id:
            sources = load_sources(DATA_DIR)
            report = create_report_from_sources("Generate incident replay from historical failure records.", equipment_id, sources)
            replay = build_incident_replay(report)
            records = [item for item in repo.failure_reports() if item.get("equipment_id") == equipment_id]
        else:
            enterprise_payload = build_enterprise_dashboard()
            replay = enterprise_payload.get("incident_replay")
            records = repo.failure_reports()[:12]
        return {"incident_replay": replay, "records": records}
    except Exception as exc:
        logger.exception("Incident replay generation failed equipment_id=%s error=%s", equipment_id, exc)
        return {"incident_replay": None, "records": [], "error": str(exc)}


@app.get("/api/operations-center")
async def operations_center():
    return safe_dashboard_payload("operations_center", build_operations_center, lambda: {"kpis": [], "top_risks": [], "fallback": True})


@app.get("/api/digital-twin")
async def digital_twin():
    return safe_dashboard_payload("digital_twin", build_plant_digital_twin, lambda: {"zones": [], "assets": repo.assets(), "fallback": True})


@app.post("/api/search")
async def semantic_search(payload: SearchRequest):
    require_ai_ready()
    return {"results": rag.retrieve(payload.query, payload.equipment_id)}


@app.post("/api/knowledge-search")
async def knowledge_search(payload: SearchRequest):
    require_ai_ready()
    sources = load_sources(DATA_DIR)
    evidence = retrieve_context(payload.query, payload.equipment_id, sources, top_n=8)
    return {"results": [item.__dict__ for item in evidence], "rag": rag.retrieve(payload.query, payload.equipment_id)}


@app.post("/api/feedback")
async def feedback(payload: dict):
    equipment_id = str(payload.get("equipment_id", "")).strip()
    feedback_text = str(payload.get("feedback", "")).strip()
    if not equipment_id or not feedback_text:
        raise HTTPException(status_code=400, detail="Equipment and feedback are required.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    append_feedback(OUTPUT_DIR, equipment_id, feedback_text)
    return {"ok": True}


@app.post("/api/what-if")
async def what_if(payload: dict):
    equipment_id = str(payload.get("equipment_id", "")).strip()
    overrides = payload.get("overrides", {})
    if not equipment_id:
        raise HTTPException(status_code=400, detail="Equipment is required.")
    if not isinstance(overrides, dict):
        raise HTTPException(status_code=400, detail="Overrides must be an object.")

    sources = load_sources(DATA_DIR)
    sensor_index = sources["sensors"].index[sources["sensors"].equipment_id == equipment_id].tolist()
    if not sensor_index:
        raise HTTPException(status_code=400, detail="Unknown equipment.")

    allowed_metrics = {
        "temperature_c",
        "vibration_mm_s",
        "motor_current_a",
        "oil_pressure_bar",
        "hydraulic_pressure_bar",
        "roll_gap_variation_mm",
        "speed_mpm",
        "operating_hours_since_service",
    }
    row_index = sensor_index[0]
    changed_metrics = []
    for metric, value in overrides.items():
        if metric not in allowed_metrics:
            continue
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            continue
        sources["sensors"].loc[row_index, metric] = numeric_value
        changed_metrics.append(f"{metric}={numeric_value:g}")

    sources["sensors"].loc[row_index, "anomaly_alert"] = "WHAT_IF_SCENARIO"
    query = (
        f"What-if maintenance scenario for {equipment_id}. Evaluate risk, RUL, "
        "recommended action, and spare impact. Changed metrics: "
        f"{', '.join(changed_metrics) if changed_metrics else 'none'}."
    )
    report = create_report_from_sources(query, equipment_id, sources)
    alerts = build_alerts_from_sources(sources)
    return {
        "report": report,
        "alerts": alerts,
        "role_notifications": build_role_notifications(alerts, sources["spares"]),
    }


@app.post("/api/work-order")
async def work_order(payload: dict):
    equipment_id = str(payload.get("equipment_id", "")).strip()
    query = str(payload.get("query", "")).strip()
    if not equipment_id:
        raise HTTPException(status_code=400, detail="Equipment is required.")
    if not query:
        query = f"Generate maintenance work order for {equipment_id} based on active alert."

    sources = load_sources(DATA_DIR)
    report = create_report_from_sources(query, equipment_id, sources)
    work_order_payload = build_work_order(report, sources)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "work_order.json").write_text(json.dumps(work_order_payload, indent=2), encoding="utf-8")
    append_audit("maintenance_engineer", "generated work order", equipment_id, work_order_payload["work_order_id"])
    return {"work_order": work_order_payload}


@app.post("/api/ingest")
async def ingest(payload: dict):
    input_type = str(payload.get("input_type", "")).strip()
    equipment_id = str(payload.get("equipment_id", "")).strip()
    content = str(payload.get("content", "")).strip()
    if not input_type or not equipment_id or not content:
        raise HTTPException(status_code=400, detail="Input type, equipment, and content are required.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "record_id": f"IN-{uuid.uuid4().hex[:8].upper()}",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "input_type": input_type,
        "equipment_id": equipment_id,
        "content": content,
        "status": "captured for reasoning and feedback loop",
    }
    with (OUTPUT_DIR / "ingested_inputs.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
    append_audit("maintenance_engineer", f"ingested {input_type}", equipment_id, record["record_id"])
    return {"ingested": record, "knowledge_center": build_knowledge_sources()}


@app.post("/api/operation-simulator")
async def operation_simulator(payload: dict):
    equipment_id = str(payload.get("equipment_id", "")).strip()
    strategy = str(payload.get("strategy", "restricted_operation")).strip()
    if not equipment_id:
        raise HTTPException(status_code=400, detail="Equipment is required.")
    result = simulate_operation_strategy(equipment_id, strategy)
    append_audit("production_supervisor", f"simulated {strategy}", equipment_id, "SIMULATION")
    return {"simulation": result}


@app.post("/api/save-work-order")
async def save_work_order(payload: dict):
    work_order_payload = payload.get("work_order")
    if not isinstance(work_order_payload, dict):
        raise HTTPException(status_code=400, detail="Work order is required.")
    status = str(payload.get("status", work_order_payload.get("status", "Open"))).strip() or "Open"
    work_order_payload["status"] = status
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUTPUT_DIR / "saved_work_orders.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(work_order_payload) + "\n")
    append_audit(
        "maintenance_planner",
        f"saved work order status {status}",
        str(work_order_payload.get("equipment_id", "")),
        str(work_order_payload.get("work_order_id", "")),
    )
    return {"saved": True, "work_order": work_order_payload}


@app.post("/api/plant-incident-demo")
async def plant_incident_demo():
    query = (
        "Plant incident demo: Rolling Mill Gearbox shows oil contamination, elevated vibration, "
        "and recurring bearing wear. Run full autonomous investigation and prepare executive output."
    )
    workflow_state = workflow.run(query, "TSA-RM-GBX-002")
    report = workflow_state["report"]
    agentic = build_agentic_payload(workflow_state)
    sources = load_sources(DATA_DIR)
    work_order_payload = build_work_order(report, sources)
    enterprise_payload = build_enterprise_dashboard()
    append_audit("demo_operator", "ran plant incident demo", report["equipment"]["equipment_id"], work_order_payload["work_order_id"])
    return {
        "report": report,
        "agentic": agentic,
        "work_order": work_order_payload,
        "enterprise": enterprise_payload,
        "alerts": build_alerts(),
    }


@app.get("/api/reports")
async def reports(report_type: str = "executive_summary", export_format: str = "json"):
    payload = build_enterprise_report(report_type)
    if export_format == "pdf":
        return Response(content=make_simple_pdf(payload["text"]), media_type="application/pdf")
    if export_format == "excel":
        return Response(content=payload["csv"], media_type="application/vnd.ms-excel")
    return payload["json"]


@app.get("/api/report-export")
async def report_export(type: str = "executive_summary", format: str = "json"):
    if "executive" in str(type).lower():
        require_ai_ready()
    return await reports(type, format)


@app.get("/api/work-order-pdf")
async def work_order_pdf():
    return Response(
        content=make_simple_pdf(build_work_order_pdf_text()),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="work_order.pdf"'},
    )


@app.get("/api/shift-handover-pdf")
async def shift_handover_pdf():
    return Response(
        content=make_simple_pdf(build_shift_handover_pdf_text()),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="shift_handover.pdf"'},
    )


@app.get("/api/executive-report-pdf")
async def executive_report_pdf():
    require_ai_ready()
    return Response(
        content=make_simple_pdf(build_executive_report_pdf_text()),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="executive_report.pdf"'},
    )


@app.get("/api/plant-command-center")
async def plant_command_center():
    return safe_dashboard_payload("plant_command_center", build_plant_command_center, lambda: {"kpis": [], "critical_assets": [], "fallback": True})


@app.get("/api/asset-context")
async def asset_context(equipment_id: str):
    started = time.perf_counter()
    try:
        value = asset_context_cache.get_or_set(equipment_id, lambda: build_asset_context(equipment_id))
    except Exception as exc:
        logger.exception("Asset context generation failed equipment_id=%s error=%s", equipment_id, exc)
        value = {"equipment_id": equipment_id, "status": "degraded", "fallback": True}
    metrics.record("asset_cache_ms", (time.perf_counter() - started) * 1000)
    return value


@app.get("/api/dependency-graph")
async def dependency_graph():
    return build_dependency_graph()


@app.get("/api/ai-pipeline")
async def ai_pipeline():
    base = build_ai_pipeline_visibility()
    rag_status = rag.health_status()
    hybrid = rag_status.get("hybrid_search", {})
    llm_status = workflow.llm.health_status()
    obs = metrics.summary()
    agent_latency = (
        obs.get("langgraph_workflow", {}).get("avg_ms")
        or obs.get("sequential_agent_workflow", {}).get("avg_ms")
        or 0
    )
    extra_stages = [
        {
            "name": "Hybrid Retrieval Score",
            "status": "completed",
            "latency_ms": hybrid.get("retrieval_time_ms", 0),
            "completed_at": datetime.now().isoformat(timespec="seconds"),
            "score": hybrid.get("hybrid_retrieval_score", 0),
        },
        {
            "name": "Reranking Time",
            "status": "completed",
            "latency_ms": hybrid.get("reranking_time_ms", 0),
            "completed_at": datetime.now().isoformat(timespec="seconds"),
            "score": hybrid.get("reranked_results", 0),
        },
        {
            "name": "Embedding Service",
            "status": rag_status.get("embedding_service", {}).get("backend", "fallback"),
            "latency_ms": 0,
            "completed_at": datetime.now().isoformat(timespec="seconds"),
        },
        {
            "name": "LLM Latency",
            "status": llm_status.get("status", "not_called"),
            "latency_ms": llm_status.get("latency_ms") or 0,
            "completed_at": datetime.now().isoformat(timespec="seconds"),
            "score": llm_status.get("token_count") or 0,
        },
        {
            "name": "Agent Latency",
            "status": workflow.health_status().get("engine", "workflow"),
            "latency_ms": agent_latency,
            "completed_at": datetime.now().isoformat(timespec="seconds"),
            "score": len(workflow.health_status().get("nodes", [])),
        },
    ]
    base["stages"] = (base.get("stages") or []) + extra_stages
    base["total_processing_ms"] = int(base.get("total_processing_ms", 0) or 0) + int(hybrid.get("retrieval_time_ms", 0) or 0)
    base["hybrid_retrieval"] = hybrid
    base["embedding_service"] = rag_status.get("embedding_service", {})
    base["reranker"] = rag_status.get("reranker", {})
    base["metrics"] = {
        "retrieval_score": hybrid.get("hybrid_retrieval_score", 0),
        "rerank_score": hybrid.get("reranked_results", 0),
        "llm_latency": llm_status.get("latency_ms") or 0,
        "agent_latency": agent_latency,
        "token_count": llm_status.get("token_count") or 0,
        "confidence_score": llm_status.get("llm_confidence_estimate", 0),
        "source_count": hybrid.get("reranked_results", 0),
    }
    base["observability"] = obs
    return base


@app.get("/api/system-health")
async def system_health():
    try:
        preload = preload_status_payload()
        warmup_status = preload.get("model_warmup") or {}
        current_rag = rag._instance if bool(getattr(rag, "loaded", False)) else None
        current_workflow = workflow._instance if bool(getattr(workflow, "loaded", False)) else None
        chroma_status = (
            current_rag.vector_store.status()
            if current_rag and current_rag.vector_store and hasattr(current_rag.vector_store, "status")
            else preload.get("vector_store", {})
        )
        document_count = int(chroma_status.get("document_count") or 0)
        vector_ready = bool(preload.get("vector_store_loaded") or (chroma_status.get("available") and document_count > 0))
        workflow_ready = bool(preload.get("workflow_loaded") or current_workflow)
        embedding_loaded = bool(current_rag and current_rag.embedding_service.model is not None)
        reranker_loaded = bool(current_rag and current_rag.reranker.model is not None)
        core_ready = bool(vector_ready and workflow_ready)
        ai_model_ready = bool((preload.get("embedding_loaded") or embedding_loaded) and (preload.get("reranker_loaded") or reranker_loaded))
        workflow_status = current_workflow.health_status() if current_workflow else {"engine": "not_loaded", "nodes": []}
        postgres_status = "healthy" if settings.enable_postgres else "disabled_json_seed_mode"
    except Exception as exc:
        return {"fastapi": "healthy", "error": str(exc), "status": "degraded"}
    return {
        "fastapi": "healthy",
        "status": "healthy" if core_ready else "initializing",
        "system_ready": core_ready,
        "ai_model_ready": ai_model_ready,
        "vector_store_ready": vector_ready,
        "workflow_ready": workflow_ready,
        "embedding_model_loaded": bool(preload.get("embedding_loaded") or embedding_loaded),
        "reranker_loaded": bool(preload.get("reranker_loaded") or reranker_loaded),
        "embedding_warming": warmup_status.get("embedding_warming", False),
        "reranker_warming": warmup_status.get("reranker_warming", False),
        "langgraph": workflow_status["engine"] if workflow_ready and workflow_status.get("engine") == "langgraph" else ("ready" if workflow_ready else "not_loaded"),
        "groq": "not_checked",
        "chromadb": "healthy" if vector_ready else "initializing",
        "qdrant": "disabled" if settings.vector_db != "qdrant" else "not_checked",
        "postgresql": postgres_status,
        "embedding_service": "loaded" if (preload.get("embedding_loaded") or embedding_loaded) else "initializing",
        "hybrid_search": "metadata_only",
        "streaming_llm": "not_checked",
        "memory_layer": "not_checked",
        "langsmith": langsmith_observer.health_status()["status"],
        "rag": "healthy" if vector_ready else "initializing",
        "documents": document_count,
        "vectors": document_count,
        "document_count": document_count,
        "vector_count": document_count,
        "agent_count": len(workflow_status.get("nodes", [])),
        "reranker": "loaded" if (preload.get("reranker_loaded") or reranker_loaded) else "initializing",
        "details": {
            "workflow": workflow_status,
            "llm": {"status": "not_checked"},
            "rag": {
                "status": "healthy" if vector_ready else "initializing",
                "documents": document_count,
                "vectors": document_count,
                "retrieval_test": "not_run",
            },
            "chromadb": chroma_status,
            "qdrant": {"status": "disabled" if settings.vector_db != "qdrant" else "not_checked"},
            "postgresql": {"status": postgres_status, "enabled": settings.enable_postgres},
            "embedding_service": {"status": "loaded" if (preload.get("embedding_loaded") or embedding_loaded) else "initializing", "real_model_loaded": bool(preload.get("embedding_loaded") or embedding_loaded)},
            "model_warmup": warmup_status,
            "hybrid_search": {"status": "metadata_only", "retrieval_test": "not_run"},
            "streaming_llm": {"status": "not_checked"},
            "memory_layer": {"status": "not_checked"},
            "langsmith": langsmith_observer.health_status(),
            "observability": metrics.summary(),
        },
    }


@app.get("/api/llm-health")
async def llm_health(run_test: bool = False):
    try:
        status = workflow.llm.diagnostic_status(run_test=run_test)
    except Exception as exc:
        status = {
            "provider": settings.llm_provider,
            "model": os.getenv("LLAMA_MODEL", "llama-3.3-70b-versatile"),
            "api_key_loaded": False,
            "connection_status": "error",
            "error": str(exc),
            "last_status": {},
        }
    return {
        "provider": status.get("provider"),
        "model": status.get("model"),
        "api_key_loaded": status.get("api_key_loaded"),
        "groq_connection_status": status.get("connection_status"),
        "latency": status.get("last_status", {}).get("latency_ms"),
        "status": status.get("connection_status"),
        "last_error": status.get("error") or status.get("last_status", {}).get("error"),
        "test_generation_result": {
            "status": status.get("connection_status"),
            "error": status.get("error"),
            "latency_ms": status.get("last_status", {}).get("latency_ms"),
            "token_count": status.get("last_status", {}).get("token_count"),
        },
        "base_url": status.get("base_url"),
        "details": status,
    }


@app.get("/api/groq-test")
async def groq_test():
    try:
        return workflow.llm.legacy_provider.groq_test()
    except Exception as exc:
        return {
            "success": False,
            "latency_ms": 0,
            "model": os.getenv("LLAMA_MODEL", "llama-3.3-70b-versatile"),
            "provider": "groq",
            "status": "error",
            "error": str(exc),
            "api_key_loaded": bool(os.getenv("GROQ_API_KEY") or os.getenv("LLAMA_API_KEY")),
        }


@app.get("/api/gemini-test")
async def gemini_test():
    try:
        return workflow.llm.legacy_provider.gemini_test()
    except Exception as exc:
        return {
            "status": "error",
            "model": os.getenv("GEMINI_MODEL"),
            "latency_ms": 0,
            "api_key_loaded": bool(os.getenv("GEMINI_API_KEY")),
            "error": str(exc),
        }


@app.get("/api/vector-health")
async def vector_health():
    try:
        current_rag = rag._instance if bool(getattr(rag, "loaded", False)) else None
        if not current_rag or not current_rag.vector_store:
            return {
                "backend": "not_loaded",
                "collection_name": None,
                "collection": None,
                "expected_collection": "maintenance_knowledge_d384",
                "document_count": 0,
                "dimension": None,
                "healthy": False,
                "ready": False,
                "retrieval_test": "not_run",
                "retrieved_count": 0,
                "retrieval_ms": None,
                "details": {"status": "vector_store_not_loaded"},
            }
        store = current_rag.vector_store
        ready = store.is_ready() if hasattr(store, "is_ready") else False
        status = store.status()
        document_count = int(status.get("document_count") or 0)
        return {
            "backend": status.get("backend"),
            "collection_name": status.get("collection"),
            "collection": status.get("collection"),
            "expected_collection": status.get("expected_collection", "maintenance_knowledge_d384"),
            "document_count": document_count,
            "dimension": status.get("embedding_dimension"),
            "healthy": bool(ready and document_count > 0),
            "ready": ready,
            "retrieval_test": "not_run",
            "retrieved_count": 0,
            "retrieval_ms": None,
            "persist_directory": status.get("persist_directory"),
            "details": status,
        }
    except Exception as exc:
        return {
            "backend": "unknown",
            "collection_name": None,
            "collection": None,
            "expected_collection": "maintenance_knowledge_d384",
            "document_count": 0,
            "dimension": None,
            "healthy": False,
            "error": str(exc),
        }


@app.get("/api/startup-health")
async def startup_health():
    preload = preload_status_payload()
    rag_loaded = bool(getattr(rag, "loaded", False))
    workflow_loaded = bool(getattr(workflow, "loaded", False))
    current_rag = rag._instance if rag_loaded else None
    vector_ready = bool(current_rag and current_rag.vector_store and getattr(current_rag.vector_store, "is_ready", lambda: False)())
    return {
        "startup_time_ms": STARTUP_DURATION_MS,
        "startup_time": round(STARTUP_DURATION_MS / 1000, 3),
        "config_load_ms": CONFIG_LOAD_MS,
        "route_registration_ms": ROUTE_REGISTRATION_MS,
        "startup_embedding_ms": preload.get("startup_embedding_ms"),
        "startup_reranker_ms": preload.get("startup_reranker_ms"),
        "startup_vectorstore_ms": preload.get("startup_vectorstore_ms"),
        "startup_workflow_ms": preload.get("startup_workflow_ms"),
        "model_timing_breakdown": preload.get("model_timing_breakdown"),
        "model_mode": preload.get("model_mode"),
        "model_cache_directory": preload.get("model_cache_directory"),
        "fallback_active": preload.get("fallback_active"),
        "retrieval_mode": preload.get("retrieval_mode"),
        "embedding_real_model_loaded": preload.get("embedding_real_model_loaded"),
        "reranker_real_model_loaded": preload.get("reranker_real_model_loaded"),
        "embedding_fallback_active": preload.get("embedding_fallback_active"),
        "reranker_fallback_active": preload.get("reranker_fallback_active"),
        "embedding_fallback_reason": preload.get("embedding_fallback_reason"),
        "reranker_fallback_reason": preload.get("reranker_fallback_reason"),
        "workflow_loaded": preload["workflow_loaded"] or workflow_loaded,
        "vector_store_loaded": vector_ready,
        "embedding_loaded": preload["embedding_loaded"],
        "reranker_loaded": preload["reranker_loaded"],
        "embedding_warming": preload.get("embedding_warming"),
        "reranker_warming": preload.get("reranker_warming"),
        "model_warmup": preload.get("model_warmup"),
        "background_tasks_running": preload["running"],
        "system_ready": preload["system_ready"],
        "lazy_loading_enabled": settings.enable_runtime_model_loading and not settings.eager_load_ai_models,
        "background_preload_enabled": settings.background_preload_ai_models,
        "background_status": preload,
        "rag_loaded": rag_loaded,
        "rag_load_ms": getattr(rag, "loaded_at_ms", None),
        "workflow_load_ms": getattr(workflow, "loaded_at_ms", None),
        "dashboard_cache": dashboard_cache.status(),
        "asset_context_cache": asset_context_cache.status(),
        "investigation_cache": investigation_cache.status(),
    }


@app.get("/api/preload-status")
async def preload_status():
    return preload_status_payload()


@app.get("/api/model-status")
async def model_status():
    status = preload_status_payload()
    return {
        "embedding_loaded": bool(status.get("embedding_loaded")),
        "reranker_loaded": bool(status.get("reranker_loaded")),
        "embedding_warming": bool(status.get("embedding_warming")),
        "reranker_warming": bool(status.get("reranker_warming")),
        "warmup_running": bool((status.get("model_warmup") or {}).get("running")),
        "ai_model_ready": bool(status.get("embedding_loaded") and status.get("reranker_loaded")),
        "model_mode": status.get("model_mode"),
        "model_cache_directory": status.get("model_cache_directory"),
        "embedding_real_model_loaded": status.get("embedding_real_model_loaded"),
        "reranker_real_model_loaded": status.get("reranker_real_model_loaded"),
        "embedding_fallback_active": status.get("embedding_fallback_active"),
        "reranker_fallback_active": status.get("reranker_fallback_active"),
        "embedding_fallback_reason": status.get("embedding_fallback_reason"),
        "reranker_fallback_reason": status.get("reranker_fallback_reason"),
        "model_warmup": status.get("model_warmup", {}),
    }


@app.get("/api/model-health")
async def model_health():
    status = preload_status_payload()
    return {
        "embedding_loaded": bool(status.get("embedding_loaded")),
        "reranker_loaded": bool(status.get("reranker_loaded")),
        "embedding_warming": bool(status.get("embedding_warming")),
        "reranker_warming": bool(status.get("reranker_warming")),
        "ai_model_ready": bool(status.get("ai_model_ready")),
        "embedding_real_model_loaded": bool(status.get("embedding_real_model_loaded")),
        "reranker_real_model_loaded": bool(status.get("reranker_real_model_loaded")),
        "fallback_active": bool(status.get("fallback_active")),
        "embedding_fallback_active": bool(status.get("embedding_fallback_active")),
        "reranker_fallback_active": bool(status.get("reranker_fallback_active")),
        "embedding_fallback_reason": status.get("embedding_fallback_reason"),
        "reranker_fallback_reason": status.get("reranker_fallback_reason"),
        "cache_directory": status.get("model_cache_directory"),
        "model_cache_directory": status.get("model_cache_directory"),
        "retrieval_mode": status.get("retrieval_mode"),
        "model_mode": status.get("model_mode"),
        "embedding_model_timing": status.get("embedding_model_timing"),
        "reranker_model_timing": status.get("reranker_model_timing"),
        "embedding_model_path": status.get("embedding_model_path"),
        "reranker_model_path": status.get("reranker_model_path"),
        "system_ready": bool(status.get("system_ready")),
    }


@app.get("/api/performance")
async def performance():
    return build_performance_payload()


@app.get("/api/performance-health")
async def performance_health():
    return build_performance_payload()


def build_performance_payload() -> dict:
    summary = metrics.summary()
    last_request = metrics.latest_request()
    preload = preload_status_payload()
    rag_loaded = bool(getattr(rag, "loaded", False))
    workflow_loaded = bool(getattr(workflow, "loaded", False))
    current_rag = rag._instance if rag_loaded else None
    current_workflow = workflow._instance if workflow_loaded else None
    rag_stats = (current_rag.last_retrieval_stats if current_rag else {}) or {}
    llm_status = current_workflow.llm.health_status() if current_workflow else {}
    workflow_summary = current_workflow.health_status() if current_workflow else {"engine": "lazy_not_loaded"}

    def avg_ms(name: str) -> float:
        return float(summary.get(name, {}).get("avg_ms", 0) or 0)

    retrieval_time = last_request.get("retrieval_ms")
    if retrieval_time is None:
        retrieval_time = rag_stats.get("retrieval_time_ms", avg_ms("rag_retrieval"))
    rerank_time = last_request.get("rerank_ms")
    if rerank_time is None:
        rerank_time = rag_stats.get("reranking_time_ms", avg_ms("rag_reranking"))
    llm_time = last_request.get("llm_ms")
    if llm_time is None:
        llm_time = llm_status.get("latency_ms") or avg_ms("executive_agent") or avg_ms("lightweight_llm_response")
    workflow_time = last_request.get("workflow_ms")
    if workflow_time is None:
        workflow_time = avg_ms("langgraph_workflow") or avg_ms("sequential_agent_workflow") or avg_ms("lightweight_workflow")
    total_request_time = last_request.get("total_request_ms")
    if total_request_time is None:
        total_request_time = workflow_time
    return {
        "startup_ms": STARTUP_DURATION_MS,
        "startup_time": round(STARTUP_DURATION_MS / 1000, 3),
        "config_load_ms": CONFIG_LOAD_MS,
        "route_registration_ms": ROUTE_REGISTRATION_MS,
        "embedding_load_time": avg_ms("embedding_model_load"),
        "reranker_load_time": avg_ms("reranker_model_load"),
        "startup_embedding_ms": preload.get("startup_embedding_ms") or avg_ms("startup_embedding_ms"),
        "startup_reranker_ms": preload.get("startup_reranker_ms") or avg_ms("startup_reranker_ms"),
        "startup_vectorstore_ms": preload.get("startup_vectorstore_ms") or avg_ms("startup_vectorstore_ms"),
        "startup_workflow_ms": preload.get("startup_workflow_ms") or avg_ms("startup_workflow_ms"),
        "model_timing_breakdown": preload.get("model_timing_breakdown"),
        "model_mode": preload.get("model_mode"),
        "model_cache_directory": preload.get("model_cache_directory"),
        "fallback_active": preload.get("fallback_active"),
        "retrieval_mode": preload.get("retrieval_mode"),
        "embedding_real_model_loaded": preload.get("embedding_real_model_loaded"),
        "reranker_real_model_loaded": preload.get("reranker_real_model_loaded"),
        "embedding_fallback_active": preload.get("embedding_fallback_active"),
        "reranker_fallback_active": preload.get("reranker_fallback_active"),
        "embedding_fallback_reason": preload.get("embedding_fallback_reason"),
        "reranker_fallback_reason": preload.get("reranker_fallback_reason"),
        "retrieval_time": retrieval_time,
        "retrieval_ms": retrieval_time,
        "rerank_time": rerank_time,
        "rerank_ms": rerank_time,
        "llm_time": llm_time,
        "llm_ms": llm_time,
        "workflow_time": workflow_time,
        "workflow_ms": workflow_time,
        "agent_time": workflow_time,
        "total_time": total_request_time,
        "total_response_time": total_request_time,
        "total_request_ms": total_request_time,
        "last_request_metrics": last_request,
        "workflow_engine": last_request.get("workflow_engine") or workflow_summary.get("engine"),
        "embedding_loaded": preload.get("embedding_loaded"),
        "reranker_loaded": preload.get("reranker_loaded"),
        "embedding_warming": preload.get("embedding_warming"),
        "reranker_warming": preload.get("reranker_warming"),
        "model_warmup": preload.get("model_warmup"),
        "vector_store_loaded": preload.get("vector_store_loaded"),
        "workflow_loaded": preload.get("workflow_loaded"),
        "system_ready": preload.get("system_ready"),
        "preload_completed": preload.get("completed"),
        "preload_running": preload.get("running"),
        "ready_progress_percent": preload.get("ready_progress_percent"),
        "token_count": llm_status.get("token_count"),
        "prompt_tokens": llm_status.get("prompt_tokens"),
        "completion_tokens": llm_status.get("completion_tokens"),
        "total_tokens": llm_status.get("total_tokens") or llm_status.get("token_count"),
        "cached_response_used": bool(last_request.get("cached_response_used")) or bool(summary.get("investigation_cache_hit", {}).get("count", 0)),
        "cache_hit_rate": investigation_cache.status().get("hit_rate", 0),
        "cache_status": {
            "rag_pipeline_singleton": True,
            "workflow_singleton": True,
            "rag_loaded": rag_loaded,
            "workflow_loaded": workflow_loaded,
            "background_tasks_running": preload["running"],
            "dashboard_cache": dashboard_cache.status(),
            "asset_context_cache": asset_context_cache.status(),
            "investigation_cache": investigation_cache.status(),
            "embedding_model_load_attempted": bool(current_rag and current_rag.embedding_service.load_attempted),
            "reranker_load_attempted": bool(current_rag and current_rag.reranker.load_attempted),
            "auto_index_vector_store": settings.auto_index_vector_store,
            "runtime_model_loading": settings.enable_runtime_model_loading,
        },
        "observability": summary,
    }


@app.websocket("/ws/sensors")
async def sensor_stream(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"type": "sensor_snapshot", "data": repo.sensors()})
    await websocket.close()


@app.websocket("/ws/alerts")
async def alert_stream(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"type": "alerts", "data": build_alerts()})
    await websocket.close()


@app.websocket("/ws/digital-twin")
async def digital_twin_stream(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"type": "digital_twin", "data": build_plant_digital_twin()})
    await websocket.close()


@app.websocket("/ws/copilot-progress")
async def copilot_progress(websocket: WebSocket):
    await websocket.accept()
    stages = [
        "Thinking...",
        "Analyzing sensor data...",
        "Retrieving Manuals...",
        "Running Hybrid RAG...",
        "Building RCA...",
        "Checking inventory tools...",
        "Generating Recommendation...",
    ]
    for index, stage in enumerate(stages, start=1):
        await websocket.send_json({"stage": stage, "status": "completed", "progress": round(index / len(stages) * 100)})
    await websocket.close()
