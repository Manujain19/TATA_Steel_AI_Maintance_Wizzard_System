from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.llm_provider import LLMProvider

from maintenance_wizard import (
    assess_risk,
    condition_breaches,
    create_report_from_sources,
    load_sources,
    matched_history,
    retrieve_context,
)


@dataclass
class AgentResult:
    agent_name: str
    started_at: str
    completed_at: str
    status: str
    progress: int
    steps: List[str]
    output: Dict[str, Any]


class BaseAgent:
    name = "Base Agent"

    def run(self, context: Dict[str, Any]) -> AgentResult:
        started = timestamp()
        steps, output = self.execute(context)
        completed = timestamp()
        return AgentResult(
            agent_name=self.name,
            started_at=started,
            completed_at=completed,
            status="success",
            progress=100,
            steps=steps,
            output=output,
        )

    def execute(self, context: Dict[str, Any]) -> tuple[List[str], Dict[str, Any]]:
        raise NotImplementedError


class SensorAgent(BaseAgent):
    name = "Sensor Analysis Agent"

    def execute(self, context: Dict[str, Any]) -> tuple[List[str], Dict[str, Any]]:
        row = context["sensor_row"]
        breaches = condition_breaches(row)
        context["breaches"] = breaches
        return (
            ["Parsed live condition monitoring data", "Detected threshold breaches"],
            {
                "breach_count": len(breaches),
                "breaches": [breach.__dict__ for breach in breaches],
            },
        )


class DiagnosisAgent(BaseAgent):
    name = "Fault Diagnosis Agent"

    def execute(self, context: Dict[str, Any]) -> tuple[List[str], Dict[str, Any]]:
        report = context["base_report"]
        return (
            ["Identified probable fault mode", "Mapped anomaly to known failure patterns"],
            {
                "probable_fault": report["diagnosis"]["probable_fault"],
                "active_alert": report["equipment"]["active_alert"],
            },
        )


class KnowledgeAgent(BaseAgent):
    name = "Knowledge Retrieval Agent"

    def execute(self, context: Dict[str, Any]) -> tuple[List[str], Dict[str, Any]]:
        evidence = retrieve_context(
            context["query"], context["equipment_id"], context["sources"], top_n=7
        )
        context["retrieved_evidence"] = evidence
        return (
            [
                "Retrieved relevant SOPs",
                "Retrieved maintenance manuals",
                "Retrieved historical failures",
            ],
            {
                "retrieval_count": len(evidence),
                "top_context": [
                    {
                        "source": item.source,
                        "title": item.title,
                        "score": item.score,
                        "detail": item.detail[:500],
                    }
                    for item in evidence
                ],
            },
        )


class RootCauseAgent(BaseAgent):
    name = "Root Cause Agent"

    def execute(self, context: Dict[str, Any]) -> tuple[List[str], Dict[str, Any]]:
        causes = context["base_report"]["diagnosis"]["probable_root_causes"]
        ranked = [
            {"cause": cause, "rank": index + 1, "confidence": max(0.58, 0.92 - index * 0.09)}
            for index, cause in enumerate(causes)
        ]
        return (
            ["Generated root cause hypotheses", "Ranked likely causes"],
            {"ranked_root_causes": ranked},
        )


class RiskAgent(BaseAgent):
    name = "Risk Assessment Agent"

    def execute(self, context: Dict[str, Any]) -> tuple[List[str], Dict[str, Any]]:
        report = context["base_report"]
        return (
            ["Calculated risk score", "Estimated urgency and impact"],
            {
                "risk": report["risk"],
                "urgency": report["priority"]["urgency"],
                "bottlenecks": report["priority"]["plant_bottleneck_priority"],
            },
        )


class SpareAgent(BaseAgent):
    name = "Spare Parts Agent"

    def execute(self, context: Dict[str, Any]) -> tuple[List[str], Dict[str, Any]]:
        spares = context["sources"]["spares"]
        equipment_id = context["equipment_id"]
        related = spares[spares.equipment_id == equipment_id]
        blockers = related[(related.available_qty <= 0) | (related.lead_time_days >= 14)]
        return (
            ["Checked inventory availability", "Evaluated lead-time risks"],
            {
                "spare_count": int(len(related)),
                "blocked_spares": [
                    {
                        "part": row.part,
                        "available_qty": int(row.available_qty),
                        "lead_time_days": int(row.lead_time_days),
                        "criticality": row.criticality,
                    }
                    for _, row in blockers.iterrows()
                ],
            },
        )


class PlannerAgent(BaseAgent):
    name = "Maintenance Planning Agent"

    def execute(self, context: Dict[str, Any]) -> tuple[List[str], Dict[str, Any]]:
        report = context["base_report"]
        return (
            ["Generated maintenance actions", "Generated inspection sequence"],
            {
                "actions": report["recommendations"],
                "inspection_sequence": [
                    "Confirm abnormal readings locally",
                    "Apply safe operating restriction",
                    "Inspect most likely root-cause component",
                    "Verify spare readiness and escalation path",
                    "Record outcome in digital log",
                ],
            },
        )


class WorkOrderAgent(BaseAgent):
    name = "Work Order Agent"

    def execute(self, context: Dict[str, Any]) -> tuple[List[str], Dict[str, Any]]:
        report = context["base_report"]
        risk_level = report["risk"]["level"]
        manpower = 5 if risk_level == "critical" else 4 if risk_level == "high" else 2
        duration = 6 if risk_level == "critical" else 4 if risk_level == "high" else 2
        cost = 145000 if risk_level == "critical" else 85000 if risk_level == "high" else 35000
        output = {
            "priority": risk_level,
            "owner": "Maintenance Engineer",
            "estimated_manpower": manpower,
            "estimated_cost_inr": cost,
            "required_skills": infer_required_skills(report),
            "shutdown_duration_hours": duration,
            "safety_classification": "high energy isolation" if risk_level in {"critical", "high"} else "standard maintenance",
        }
        context["agent_work_order_fields"] = output
        return (
            ["Created work order", "Assigned priority and ownership"],
            output,
        )


class AgentOrchestrator:
    def __init__(self, data_dir: Path, llm_provider: Optional[LLMProvider] = None) -> None:
        self.data_dir = data_dir
        self.llm_provider = llm_provider or LLMProvider()
        self.agents = [
            SensorAgent(),
            DiagnosisAgent(),
            KnowledgeAgent(),
            RootCauseAgent(),
            RiskAgent(),
            SpareAgent(),
            PlannerAgent(),
            WorkOrderAgent(),
        ]

    def run(self, query: str, equipment_id: Optional[str]) -> Dict[str, Any]:
        sources = load_sources(self.data_dir)
        base_report = create_report_from_sources(query, equipment_id, sources)
        selected_id = base_report["equipment"]["equipment_id"]
        sensor_row = sources["sensors"][sources["sensors"].equipment_id == selected_id].iloc[0]
        history_matches = matched_history(selected_id, query, sources["history"])
        context: Dict[str, Any] = {
            "query": query,
            "equipment_id": selected_id,
            "sources": sources,
            "sensor_row": sensor_row,
            "base_report": base_report,
            "history_matches": history_matches,
        }

        execution = []
        for agent in self.agents:
            result = agent.run(context)
            execution.append(result.__dict__)

        llm_payload = self._build_llm_payload(base_report, context)
        llm_output = self.llm_provider.generate_json(LLM_PROMPT, llm_payload)
        confidence = calculate_confidence(base_report, context, llm_output)
        reasoning_trace = build_reasoning_trace(base_report, context, confidence)
        metrics = build_agent_metrics(execution, confidence, context)

        return {
            "base_report": base_report,
            "agent_execution": execution,
            "reasoning_trace": reasoning_trace,
            "llm_output": llm_output,
            "ai_confidence": confidence,
            "executive_ai_summary": build_consistent_executive_summary(base_report, context),
            "agent_metrics": metrics,
            "agent_work_order_fields": context.get("agent_work_order_fields", {}),
            "llm_provider": "Maintenance Wizard Intelligence Engine",
        }

    def _build_llm_payload(self, report: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        evidence = context.get("retrieved_evidence", [])
        return {
            "base_report": report,
            "sensor_values": context["sensor_row"].to_dict(),
            "historical_failures": context["history_matches"].to_dict(orient="records"),
            "retrieved_context": [
                {
                    "source": item.source,
                    "title": item.title,
                    "score": item.score,
                    "detail": item.detail[:800],
                }
                for item in evidence
            ],
        }


LLM_PROMPT = """
You are an agentic AI maintenance assistant for steel hot rolling equipment.
Generate strict JSON with these keys:
fault_diagnosis, root_cause_candidates, risk_explanation,
maintenance_recommendations, executive_summary, llm_confidence_estimate.
Use the sensor values, historical failures, SOP context, manuals, and spares.
"""


def timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def calculate_confidence(
    report: Dict[str, Any], context: Dict[str, Any], llm_output: Dict[str, Any]
) -> Dict[str, Any]:
    evidence = context.get("retrieved_evidence", [])
    breaches = report["diagnosis"]["condition_breaches"]
    history_matches = context["history_matches"]
    retrieval_score = min(1.0, sum(item.score for item in evidence) / 32.0) if evidence else 0.0
    history_score = min(1.0, len(history_matches) / 3.0)
    anomaly_score = min(1.0, len(breaches) / 4.0)
    llm_score = float(llm_output.get("llm_confidence_estimate", 0.78))
    combined = retrieval_score * 0.28 + history_score * 0.24 + anomaly_score * 0.28 + llm_score * 0.20
    return {
        "score": round(combined * 100),
        "retrieval_relevance": round(retrieval_score * 100),
        "historical_match_rate": round(history_score * 100),
        "sensor_anomaly_severity": round(anomaly_score * 100),
        "llm_confidence_estimate": round(llm_score * 100),
    }


def build_reasoning_trace(
    report: Dict[str, Any], context: Dict[str, Any], confidence: Dict[str, Any]
) -> Dict[str, Any]:
    breaches = report["diagnosis"]["condition_breaches"]
    evidence = context.get("retrieved_evidence", [])
    observed = [
        f"{item['metric']} = {item['value']} breached {item['level']} limit {item['limit']}"
        for item in breaches
    ]
    retrieved = [f"{item.source}: {item.title}" for item in evidence[:5]]
    causes = report["diagnosis"]["probable_root_causes"]
    reasoning = [
        f"Active alert {report['equipment']['active_alert']} maps to known failure patterns.",
        f"Likely root causes are {', '.join(causes) if causes else 'not yet confirmed'}.",
        f"Risk score {report['risk']['score']} is driven by condition, history, and spare constraints.",
    ]
    return {
        "observed_evidence": observed,
        "retrieved_context": retrieved,
        "reasoning": reasoning,
        "diagnosis_confidence": confidence["score"],
    }


def build_agent_metrics(
    execution: List[Dict[str, Any]], confidence: Dict[str, Any], context: Dict[str, Any]
) -> Dict[str, Any]:
    success = sum(1 for item in execution if item["status"] == "success")
    return {
        "agent_success_rate": round(success / max(len(execution), 1) * 100),
        "average_diagnosis_confidence": confidence["score"],
        "knowledge_retrieval_accuracy": confidence["retrieval_relevance"],
        "work_orders_generated": 1,
        "historical_match_rate": confidence["historical_match_rate"],
    }


def build_summary(report: Dict[str, Any]) -> str:
    causes = ", ".join(report["diagnosis"]["probable_root_causes"])
    first_action = report["recommendations"][0] if report["recommendations"] else "Escalate to maintenance review."
    return (
        f"{report['equipment']['equipment_name']} is at {report['risk']['level']} risk. "
        f"Probable fault is {report['diagnosis']['probable_fault']}; likely causes: {causes}. "
        f"{first_action}"
    )


def build_consistent_executive_summary(report: Dict[str, Any], context: Dict[str, Any]) -> str:
    equipment = report["equipment"]
    diagnosis = report["diagnosis"]
    risk = report["risk"]
    breaches = diagnosis.get("condition_breaches", [])
    causes = diagnosis.get("probable_root_causes", [])
    history = context.get("history_matches")
    history_ids = []
    if history is not None and not history.empty:
      history_ids = [str(row.case_id) for _, row in history.head(2).iterrows() if hasattr(row, "case_id")]
    spares = context["sources"]["spares"]
    related = spares[spares.equipment_id == equipment["equipment_id"]]
    blockers = related[(related.available_qty <= 0) | (related.lead_time_days >= 14)]
    breach_text = (
        ", ".join(f"{item['metric']} {item['value']}" for item in breaches[:3])
        if breaches
        else "current condition indicators"
    )
    history_text = (
        f"Historical failures {', '.join(history_ids)} indicate similar progression."
        if history_ids
        else "No close historical failure match was found, so the recommendation relies on current condition evidence."
    )
    spare_text = ""
    if not blockers.empty:
        parts = [
            f"{row.part} stock {int(row.available_qty)}, lead time {int(row.lead_time_days)} days"
            for _, row in blockers.head(2).iterrows()
        ]
        spare_text = " Spare availability risk is elevated because " + "; ".join(parts) + "."
    action = report["recommendations"][0] if report["recommendations"] else "Continue controlled monitoring with maintenance review."
    return (
        f"{str(risk['level']).title()} {equipment['active_alert']} detected on {equipment['equipment_name']} "
        f"with risk score {risk['score']}. Evidence indicates {breach_text}. "
        f"{history_text} Likely root cause candidates include "
        f"{', '.join(causes) if causes else 'field confirmation pending'}. "
        f"{action}{spare_text}"
    )


def infer_required_skills(report: Dict[str, Any]) -> List[str]:
    text = " ".join(report["recommendations"]).lower()
    skills = ["mechanical inspection", "maintenance safety"]
    if "hydraulic" in text or "pressure" in text:
        skills.append("hydraulic troubleshooting")
    if "bearing" in text or "vibration" in text:
        skills.append("vibration analysis")
    if "procurement" in text or "spare" in text:
        skills.append("spare planning")
    return list(dict.fromkeys(skills))
