from __future__ import annotations

import logging
import asyncio
from datetime import datetime
import time
from typing import Any, Dict, List, TypedDict

from backend.config import DATA_DIR, settings
from backend.memory.conversation_memory import ConversationMemory
from backend.rag.pipeline import RagPipeline
from backend.services.llm_router import LLMRouter
from backend.telemetry.langsmith import langsmith_observer
from backend.telemetry.observability import metrics
from backend.agents.tool_agents import ExecutiveAgent, InventoryAgent, RootCauseToolAgent, WorkOrderAgent
from src.maintenance_wizard import create_report

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict, total=False):
    query: str
    equipment_id: str | None
    report: Dict[str, Any]
    retrieval: Dict[str, Any]
    memory: List[Dict[str, Any]]
    diagnosis: Dict[str, Any]
    root_causes: List[str]
    maintenance_plan: List[str]
    inventory_plan: Dict[str, Any]
    tool_results: Dict[str, Any]
    executive_summary: str
    llm_output: Dict[str, Any]
    final_response: str
    execution_trace: List[Dict[str, Any]]
    workflow_engine: str
    workflow_status: str


class MaintenanceLangGraphWorkflow:
    """Agentic workflow with LangGraph execution and a safe sequential fallback."""

    def __init__(self, rag: RagPipeline | None = None) -> None:
        self.rag = rag or RagPipeline()
        self.memory = ConversationMemory()
        self.llm = LLMRouter()
        self.work_order_tool_agent = WorkOrderAgent()
        self.inventory_tool_agent = InventoryAgent()
        self.root_cause_tool_agent = RootCauseToolAgent()
        self.executive_tool_agent = ExecutiveAgent()
        self.graph = self._build_graph() if settings.enable_langgraph else None

    def _build_graph(self):
        try:
            from langgraph.graph import END, StateGraph

            graph = StateGraph(WorkflowState)
            graph.add_node("retriever_agent", self.retriever_agent)
            graph.add_node("diagnosis_agent", self.diagnosis_agent)
            graph.add_node("root_cause_agent", self.root_cause_agent)
            graph.add_node("maintenance_planner_agent", self.maintenance_planner_agent)
            graph.add_node("inventory_agent", self.inventory_agent)
            graph.add_node("executive_agent", self.executive_agent)
            graph.add_node("response_node", self.response_node)
            graph.set_entry_point("retriever_agent")
            graph.add_edge("retriever_agent", "diagnosis_agent")
            graph.add_edge("diagnosis_agent", "root_cause_agent")
            graph.add_edge("root_cause_agent", "maintenance_planner_agent")
            graph.add_edge("maintenance_planner_agent", "inventory_agent")
            graph.add_edge("inventory_agent", "executive_agent")
            graph.add_edge("executive_agent", "response_node")
            graph.add_edge("response_node", END)
            logger.info("LangGraph workflow compiled successfully")
            return graph.compile()
        except Exception as exc:
            logger.warning("LangGraph unavailable; using sequential workflow fallback: %s", exc)
            return None

    def run(self, query: str, equipment_id: str | None) -> Dict[str, Any]:
        started = time.perf_counter()
        logger.info("Copilot request received")
        logger.info("Asset selected: %s", equipment_id or "auto")
        state: WorkflowState = {
            "query": query,
            "equipment_id": equipment_id,
            "execution_trace": [],
            "workflow_engine": "langgraph" if self.graph else "sequential_fallback",
            "tool_results": {},
        }
        if self.graph:
            with metrics.span("langgraph_workflow"):
                state = self.graph.invoke(state)
        else:
            with metrics.span("sequential_agent_workflow"):
                state = self._run_sequential(state)
        state["workflow_status"] = "healthy"
        total_ms = round((time.perf_counter() - started) * 1000, 2)
        state["total_request_ms"] = total_ms
        state["workflow_ms"] = total_ms
        state["retrieval_ms"] = state.get("retrieval", {}).get("hybrid_retrieval", {}).get("retrieval_time_ms")
        state["rerank_ms"] = state.get("retrieval", {}).get("hybrid_retrieval", {}).get("reranking_time_ms")
        state["llm_ms"] = state.get("llm_output", {}).get("llm_status", {}).get("latency_ms")
        logger.info(
            "Workflow timing workflow_ms=%s retrieval_ms=%s rerank_ms=%s llm_ms=%s total_request_ms=%s",
            state["workflow_ms"],
            state["retrieval_ms"],
            state["rerank_ms"],
            state["llm_ms"],
            total_ms,
        )
        self._record_request_metrics(state, "workflow")
        self.memory.append(state.get("equipment_id") or "unknown", {"query": query, "response": state.get("final_response")})
        logger.info("Copilot response generated workflow_engine=%s", state.get("workflow_engine"))
        return dict(state)

    def run_lightweight(self, query: str, equipment_id: str | None) -> Dict[str, Any]:
        started = time.perf_counter()
        state: WorkflowState = {
            "query": query,
            "equipment_id": equipment_id,
            "execution_trace": [],
            "workflow_engine": "lightweight_chat",
            "tool_results": {},
            "retrieval_top_k": 3,
        }
        state = self.retriever_agent(state)
        prompt = "Answer maintenance copilot question using retrieved context, selected asset, and memory."
        with metrics.span("lightweight_llm_response"):
            state["llm_output"] = self.llm.generate_json(prompt, dict(state))
        state["final_response"] = (
            state["llm_output"].get("executive_summary")
            or state["report"]["recommendations"][0]
        )
        state["workflow_status"] = "healthy"
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        state["total_request_ms"] = duration_ms
        state["workflow_ms"] = duration_ms
        state["retrieval_ms"] = state.get("retrieval", {}).get("hybrid_retrieval", {}).get("retrieval_time_ms")
        state["rerank_ms"] = state.get("retrieval", {}).get("hybrid_retrieval", {}).get("reranking_time_ms")
        state["llm_ms"] = state.get("llm_output", {}).get("llm_status", {}).get("latency_ms")
        logger.info(
            "Lightweight timing workflow_ms=%s retrieval_ms=%s rerank_ms=%s llm_ms=%s total_request_ms=%s",
            state["workflow_ms"],
            state["retrieval_ms"],
            state["rerank_ms"],
            state["llm_ms"],
            duration_ms,
        )
        metrics.record("lightweight_workflow", duration_ms)
        self._record_request_metrics(state, "chat")
        self.memory.append(state.get("equipment_id") or "unknown", {"query": query, "response": state.get("final_response")})
        logger.info("Lightweight chat workflow completed duration_ms=%s", duration_ms)
        return dict(state)

    async def run_investigation_async(self, query: str, equipment_id: str | None) -> Dict[str, Any]:
        if self.graph:
            return self.run(query, equipment_id)
        started = time.perf_counter()
        state: WorkflowState = {
            "query": query,
            "equipment_id": equipment_id,
            "execution_trace": [],
            "workflow_engine": "parallel_sequential_fallback",
            "tool_results": {},
        }
        state = self.retriever_agent(state)
        state = self.diagnosis_agent(state)

        async def timed_tool(name: str, status_label: str, fn):
            node_started = time.perf_counter()
            result = await asyncio.to_thread(fn)
            duration_ms = round((time.perf_counter() - node_started) * 1000, 2)
            state.setdefault("execution_trace", []).append(
                {
                    "agent": name,
                    "status": status_label,
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "duration_ms": duration_ms,
                    "execution_status": "completed",
                }
            )
            metrics.record(name, duration_ms)
            return name, result

        report = state["report"]
        root_task = timed_tool("root_cause_agent", "Root Cause Agent Completed", lambda: self.root_cause_tool_agent.run(report, query))
        work_task = timed_tool("maintenance_planner_agent", "Maintenance Planner Completed", lambda: self.work_order_tool_agent.run(report, query))
        inventory_task = timed_tool("inventory_agent", "Inventory Agent Completed", lambda: self.inventory_tool_agent.run(report, query))
        for name, result in await asyncio.gather(root_task, work_task, inventory_task):
            if name == "root_cause_agent":
                state["root_causes"] = report["diagnosis"]["probable_root_causes"]
                state.setdefault("tool_results", {})["root_cause_agent"] = result
            elif name == "maintenance_planner_agent":
                state["maintenance_plan"] = report["recommendations"]
                state.setdefault("tool_results", {})["work_order_agent"] = result
            elif name == "inventory_agent":
                state["inventory_plan"] = result
                state.setdefault("tool_results", {})["inventory_agent"] = result

        state = self.executive_agent(state)
        state = self.response_node(state)
        state["workflow_status"] = "healthy"
        total_ms = round((time.perf_counter() - started) * 1000, 2)
        state["total_request_ms"] = total_ms
        state["workflow_ms"] = total_ms
        state["retrieval_ms"] = state.get("retrieval", {}).get("hybrid_retrieval", {}).get("retrieval_time_ms")
        state["rerank_ms"] = state.get("retrieval", {}).get("hybrid_retrieval", {}).get("reranking_time_ms")
        state["llm_ms"] = state.get("llm_output", {}).get("llm_status", {}).get("latency_ms")
        metrics.record("parallel_investigation_workflow", total_ms)
        self._record_request_metrics(state, "investigation")
        self.memory.append(state.get("equipment_id") or "unknown", {"query": query, "response": state.get("final_response")})
        logger.info("Parallel investigation workflow completed duration_ms=%s", total_ms)
        return dict(state)

    def _record_request_metrics(self, state: WorkflowState, request_type: str) -> None:
        retrieval = state.get("retrieval", {}).get("hybrid_retrieval", {}) or {}
        llm_status = state.get("llm_output", {}).get("llm_status", {}) or {}
        metrics.record_request(
            request_type=request_type,
            equipment_id=state.get("equipment_id"),
            workflow_engine=state.get("workflow_engine"),
            retrieval_ms=state.get("retrieval_ms") if state.get("retrieval_ms") is not None else retrieval.get("retrieval_time_ms"),
            rerank_ms=state.get("rerank_ms") if state.get("rerank_ms") is not None else retrieval.get("reranking_time_ms"),
            llm_ms=state.get("llm_ms") if state.get("llm_ms") is not None else llm_status.get("latency_ms"),
            workflow_ms=state.get("workflow_ms"),
            total_request_ms=state.get("total_request_ms"),
            cached_response_used=bool(retrieval.get("cache_hit")),
            bm25_results=retrieval.get("bm25_results"),
            vector_results=retrieval.get("vector_results"),
            reranked_results=retrieval.get("reranked_results"),
        )

    def _run_sequential(self, state: WorkflowState) -> WorkflowState:
        for node in [
            self.retriever_agent,
            self.diagnosis_agent,
            self.root_cause_agent,
            self.maintenance_planner_agent,
            self.inventory_agent,
            self.executive_agent,
            self.response_node,
        ]:
            state = node(state)
        return state

    def _node(self, state: WorkflowState, name: str, status_label: str, fn) -> WorkflowState:
        started = datetime.now()
        logger.info("%s started", name)
        with metrics.span(name):
            state = fn(state)
        completed = datetime.now()
        state.setdefault("execution_trace", []).append(
            {
                "agent_name": status_label,
                "node": name,
                "started_at": started.isoformat(timespec="seconds"),
                "completed_at": completed.isoformat(timespec="seconds"),
                "status": "success",
                "progress": 100,
                "steps": [f"{status_label}"],
                "output": {},
            }
        )
        duration_ms = round((completed - started).total_seconds() * 1000, 2)
        langsmith_observer.record_event(
            "agent_node",
            {
                "node": name,
                "latency_ms": duration_ms,
                "status": "success",
                "equipment_id": state.get("equipment_id"),
            },
        )
        logger.info("%s completed duration_ms=%s", name, duration_ms)
        return state

    def retriever_agent(self, state: WorkflowState) -> WorkflowState:
        def run(inner: WorkflowState) -> WorkflowState:
            report = create_report(inner["query"], inner.get("equipment_id"), DATA_DIR)
            inner["report"] = report
            inner["equipment_id"] = report["equipment"]["equipment_id"]
            inner["memory"] = self.memory.load(inner["equipment_id"])
            inner["retrieval"] = self.rag.assemble_context(
                inner["query"],
                inner.get("equipment_id"),
                top_k=int(inner.get("retrieval_top_k", 6) or 6),
            )
            documents = inner["retrieval"].get("documents", [])
            logger.info("Retriever Agent selected_asset=%s retrieved_documents=%s", inner["equipment_id"], len(documents))
            return inner

        return self._node(state, "retriever_agent", "Retriever Agent Completed", run)

    def diagnosis_agent(self, state: WorkflowState) -> WorkflowState:
        def run(inner: WorkflowState) -> WorkflowState:
            inner["diagnosis"] = inner["report"]["diagnosis"]
            return inner

        return self._node(state, "diagnosis_agent", "Diagnosis Agent Completed", run)

    def root_cause_agent(self, state: WorkflowState) -> WorkflowState:
        def run(inner: WorkflowState) -> WorkflowState:
            inner["root_causes"] = inner["report"]["diagnosis"]["probable_root_causes"]
            inner.setdefault("tool_results", {})["root_cause_agent"] = self.root_cause_tool_agent.run(inner["report"], inner["query"])
            return inner

        return self._node(state, "root_cause_agent", "Root Cause Agent Completed", run)

    def maintenance_planner_agent(self, state: WorkflowState) -> WorkflowState:
        def run(inner: WorkflowState) -> WorkflowState:
            inner["maintenance_plan"] = inner["report"]["recommendations"]
            inner.setdefault("tool_results", {})["work_order_agent"] = self.work_order_tool_agent.run(inner["report"], inner["query"])
            return inner

        return self._node(state, "maintenance_planner_agent", "Maintenance Planner Completed", run)

    def inventory_agent(self, state: WorkflowState) -> WorkflowState:
        def run(inner: WorkflowState) -> WorkflowState:
            inner["inventory_plan"] = self.inventory_tool_agent.run(inner["report"], inner["query"])
            inner.setdefault("tool_results", {})["inventory_agent"] = inner["inventory_plan"]
            return inner

        return self._node(state, "inventory_agent", "Inventory Agent Completed", run)

    def executive_agent(self, state: WorkflowState) -> WorkflowState:
        def run(inner: WorkflowState) -> WorkflowState:
            prompt = "Generate final maintenance copilot response from diagnosis, RAG context, and memory."
            inner.setdefault("tool_results", {})["executive_agent"] = self.executive_tool_agent.run(inner["report"], inner["query"])
            inner["llm_output"] = self.llm.generate_json(prompt, dict(inner))
            logger.info("LLM response generated")
            inner["executive_summary"] = (
                inner["llm_output"].get("executive_summary")
                or inner["report"]["recommendations"][0]
            )
            return inner

        return self._node(state, "executive_agent", "Executive Agent Completed", run)

    def response_node(self, state: WorkflowState) -> WorkflowState:
        def run(inner: WorkflowState) -> WorkflowState:
            inner["final_response"] = inner.get("executive_summary") or inner["report"]["recommendations"][0]
            return inner

        return self._node(state, "response_node", "Response Generated", run)

    def health_status(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "engine": "langgraph" if self.graph else "sequential_fallback",
            "nodes": [
                "Asset Context Node",
                "Retriever Agent",
                "Diagnosis Agent",
                "Root Cause Agent",
                "Maintenance Planner Agent",
                "Inventory Agent",
                "Executive Agent",
                "Response Node",
            ],
            "tool_calling": {
                "Work Order Agent": ["generate_work_order", "assign_priority", "estimate_duration"],
                "Inventory Agent": ["check_stock", "recommend_spares", "calculate_lead_time"],
                "Root Cause Agent": ["retrieve_failures", "compare_failure_patterns", "generate_rca"],
                "Executive Agent": ["business_impact", "risk_exposure", "executive_summary"],
            },
            "langsmith": langsmith_observer.health_status(),
        }
