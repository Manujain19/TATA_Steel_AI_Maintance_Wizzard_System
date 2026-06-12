from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from backend.config import DATA_DIR
from src.maintenance_wizard import load_sources, matched_history
from src.web_app import build_failure_cost_impact, build_work_order

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    tool: str
    status: str
    output: Dict[str, Any]


def generate_work_order(report: Dict[str, Any]) -> Dict[str, Any]:
    return build_work_order(report, load_sources(DATA_DIR))


def assign_priority(report: Dict[str, Any]) -> Dict[str, Any]:
    risk = report.get("risk", {})
    score = float(risk.get("score", 0) or 0)
    if score >= 80:
        priority = "P1"
    elif score >= 60:
        priority = "P2"
    elif score >= 35:
        priority = "P3"
    else:
        priority = "P4"
    return {"priority": priority, "risk_level": risk.get("level"), "risk_score": score}


def estimate_duration(report: Dict[str, Any]) -> Dict[str, Any]:
    level = str(report.get("risk", {}).get("level", "medium")).lower()
    duration = {"critical": 8, "high": 5, "medium": 3, "low": 1.5}.get(level, 3)
    return {"estimated_duration_hours": duration, "basis": f"{level} maintenance risk"}


def check_stock(report: Dict[str, Any]) -> Dict[str, Any]:
    sources = load_sources(DATA_DIR)
    equipment_id = report["equipment"]["equipment_id"]
    rows = sources["spares"][sources["spares"].equipment_id == equipment_id]
    return {
        "equipment_id": equipment_id,
        "parts": [
            {
                "part": row.part,
                "available_qty": int(row.available_qty),
                "lead_time_days": int(row.lead_time_days),
                "criticality": row.criticality,
            }
            for _, row in rows.iterrows()
        ],
    }


def recommend_spares(report: Dict[str, Any]) -> Dict[str, Any]:
    stock = check_stock(report)
    recommendations = [
        {**part, "recommended_quantity": max(1, 2 - int(part["available_qty"]))}
        for part in stock["parts"]
        if int(part["available_qty"]) <= 1 or int(part["lead_time_days"]) >= 14
    ]
    return {"spare_recommendations": recommendations}


def calculate_lead_time(report: Dict[str, Any]) -> Dict[str, Any]:
    stock = check_stock(report)
    lead_times = [int(item["lead_time_days"]) for item in stock["parts"]]
    return {"max_lead_time_days": max(lead_times) if lead_times else 0, "parts_checked": len(lead_times)}


def retrieve_failures(report: Dict[str, Any], query: str) -> Dict[str, Any]:
    sources = load_sources(DATA_DIR)
    history = matched_history(report["equipment"]["equipment_id"], query, sources["history"])
    return {"matching_failures": history.head(5).to_dict(orient="records")}


def compare_failure_patterns(report: Dict[str, Any], query: str) -> Dict[str, Any]:
    matches = retrieve_failures(report, query)["matching_failures"]
    fault = report["diagnosis"]["probable_fault"]
    return {
        "pattern": fault,
        "match_count": len(matches),
        "similarity_basis": "shared asset, alert, probable fault, and historical symptom overlap",
    }


def generate_rca(report: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "probable_fault": report["diagnosis"]["probable_fault"],
        "root_causes": report["diagnosis"]["probable_root_causes"],
        "condition_breaches": report["diagnosis"]["condition_breaches"],
    }


def business_impact(report: Dict[str, Any]) -> Dict[str, Any]:
    return build_failure_cost_impact(report)


def risk_exposure(report: Dict[str, Any]) -> Dict[str, Any]:
    impact = business_impact(report)
    return {
        "risk_level": report["risk"]["level"],
        "risk_score": report["risk"]["score"],
        "total_risk_exposure_inr": impact.get("total_risk_exposure_inr"),
    }


def executive_summary(report: Dict[str, Any]) -> Dict[str, Any]:
    action = report["recommendations"][0] if report.get("recommendations") else "Escalate to maintenance review."
    return {
        "summary": (
            f"{report['equipment']['equipment_name']} has {report['risk']['level']} risk from "
            f"{report['diagnosis']['probable_fault']}. {action}"
        )
    }


class ToolCallingAgent:
    name = "Tool Calling Agent"
    tools: Dict[str, Callable[..., Dict[str, Any]]] = {}

    def run(self, report: Dict[str, Any], query: str) -> Dict[str, Any]:
        calls: List[ToolCall] = []
        for name, tool in self.tools.items():
            try:
                if name in {"retrieve_failures", "compare_failure_patterns"}:
                    output = tool(report, query)
                else:
                    output = tool(report)
                calls.append(ToolCall(name, "success", output))
                logger.info("Tool call completed agent=%s tool=%s", self.name, name)
            except Exception as exc:
                calls.append(ToolCall(name, "error", {"error": str(exc)}))
                logger.warning("Tool call failed agent=%s tool=%s error=%s", self.name, name, exc)
        return {
            "agent": self.name,
            "status": "completed" if all(item.status == "success" for item in calls) else "degraded",
            "tool_calls": [item.__dict__ for item in calls],
        }


class WorkOrderAgent(ToolCallingAgent):
    name = "Work Order Agent"
    tools = {
        "generate_work_order": generate_work_order,
        "assign_priority": assign_priority,
        "estimate_duration": estimate_duration,
    }


class InventoryAgent(ToolCallingAgent):
    name = "Inventory Agent"
    tools = {
        "check_stock": check_stock,
        "recommend_spares": recommend_spares,
        "calculate_lead_time": calculate_lead_time,
    }


class RootCauseToolAgent(ToolCallingAgent):
    name = "Root Cause Agent"
    tools = {
        "retrieve_failures": retrieve_failures,
        "compare_failure_patterns": compare_failure_patterns,
        "generate_rca": generate_rca,
    }


class ExecutiveAgent(ToolCallingAgent):
    name = "Executive Agent"
    tools = {
        "business_impact": business_impact,
        "risk_exposure": risk_exposure,
        "executive_summary": executive_summary,
    }
