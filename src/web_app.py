from __future__ import annotations

import argparse
import csv
import json
import math
import mimetypes
import sys
import uuid
from datetime import datetime, timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from maintenance_wizard import (
    append_digital_log,
    append_feedback,
    condition_breaches,
    create_report,
    create_report_from_sources,
    load_sources,
    rank_bottlenecks,
    retrieve_context,
    risk_level as classify_risk_score,
    run_demo,
    SEVERITY_SCORE,
    write_alert_report,
    write_markdown_report,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT_DIR / "web"
DATA_DIR = ROOT_DIR / "data"
OUT_DIR = ROOT_DIR / "outputs"
BRAND_NAME = "Maintenance Wizard - Tata Steel AI Platform"
BRAND_SUBTITLE = "AI-Powered Industrial Reliability & Maintenance Intelligence"

ROLE_DEFINITIONS = [
    {
        "role": "Maintenance Engineer",
        "focus": "diagnosis, inspection, corrective action",
    },
    {
        "role": "Production Supervisor",
        "focus": "downtime risk, line restriction, restart decisions",
    },
    {
        "role": "Procurement Owner",
        "focus": "spares availability and lead-time escalation",
    },
]


class MaintenanceWizardHandler(BaseHTTPRequestHandler):
    server_version = "MaintenanceWizard/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.serve_file(WEB_DIR / "index.html")
            return
        if parsed.path.startswith("/static/"):
            self.serve_file(WEB_DIR / parsed.path.removeprefix("/static/"))
            return
        if parsed.path == "/api/bootstrap":
            self.send_json(build_bootstrap())
            return
        if parsed.path == "/api/alerts":
            self.send_json(build_alerts())
            return
        if parsed.path == "/api/live":
            self.send_json(build_live_monitor())
            return
        if parsed.path == "/api/intelligence":
            self.send_json(build_intelligence())
            return
        if parsed.path == "/api/knowledge-center":
            self.send_json(build_knowledge_sources())
            return
        if parsed.path == "/api/enterprise":
            self.send_json(build_enterprise_dashboard())
            return
        if parsed.path == "/api/incident-replay":
            query = parse_qs(parsed.query)
            equipment_id = query.get("equipment_id", [""])[0]
            self.send_json(build_incident_replay_payload(equipment_id))
            return
        if parsed.path == "/api/asset-context":
            query = parse_qs(parsed.query)
            equipment_id = query.get("equipment_id", [""])[0]
            self.send_json(build_asset_context(equipment_id))
            return
        if parsed.path == "/api/operations-center":
            self.send_json(build_operations_center())
            return
        if parsed.path == "/api/plant-command-center":
            self.send_json(build_plant_command_center())
            return
        if parsed.path == "/api/digital-twin":
            self.send_json(build_plant_digital_twin())
            return
        if parsed.path == "/api/dependency-graph":
            self.send_json(build_dependency_graph())
            return
        if parsed.path == "/api/ai-pipeline":
            self.send_json(build_ai_pipeline_visibility())
            return
        if parsed.path == "/api/report-export":
            self.handle_report_export(parsed.query)
            return
        if parsed.path == "/api/work-order-pdf":
            self.send_pdf("work_order.pdf", build_work_order_pdf_text())
            return
        if parsed.path == "/api/shift-handover-pdf":
            self.send_pdf("shift_handover.pdf", build_shift_handover_pdf_text())
            return
        if parsed.path == "/api/executive-report-pdf":
            self.send_pdf("executive_report.pdf", build_executive_report_pdf_text())
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = self.read_json()
            if parsed.path == "/api/analyze":
                self.handle_analyze(payload)
                return
            if parsed.path == "/api/demo":
                self.handle_demo()
                return
            if parsed.path == "/api/feedback":
                self.handle_feedback(payload)
                return
            if parsed.path == "/api/what-if":
                self.handle_what_if(payload)
                return
            if parsed.path == "/api/work-order":
                self.handle_work_order(payload)
                return
            if parsed.path == "/api/knowledge-search":
                self.handle_knowledge_search(payload)
                return
            if parsed.path == "/api/ingest":
                self.handle_ingest(payload)
                return
            if parsed.path == "/api/chat":
                self.handle_chat(payload)
                return
            if parsed.path == "/api/operation-simulator":
                self.handle_operation_simulator(payload)
                return
            if parsed.path == "/api/save-work-order":
                self.handle_save_work_order(payload)
                return
            if parsed.path == "/api/plant-incident-demo":
                self.handle_plant_incident_demo()
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
        except ValueError as exc:
            self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:  # pragma: no cover - browser-facing guardrail
            self.send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def handle_analyze(self, payload: dict) -> None:
        query = str(payload.get("query", "")).strip()
        equipment_id = str(payload.get("equipment_id", "")).strip() or None
        feedback = str(payload.get("feedback", "")).strip() or None
        if not query:
            raise ValueError("Query is required.")

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        agentic = run_agentic_analysis(query, equipment_id)
        report = agentic["base_report"]
        sources = load_sources(DATA_DIR)
        work_order = build_work_order(report, sources)
        failure_cost_impact = build_failure_cost_impact(report)
        (OUT_DIR / "maintenance_report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        (OUT_DIR / "agentic_report.json").write_text(
            json.dumps(agentic, indent=2), encoding="utf-8"
        )
        (OUT_DIR / "work_order.json").write_text(
            json.dumps(work_order, indent=2), encoding="utf-8"
        )
        write_markdown_report(report, OUT_DIR / "maintenance_report.md")
        write_alert_report(DATA_DIR, OUT_DIR / "alert_report.csv")
        append_digital_log(OUT_DIR, report)
        append_audit("maintenance_engineer", "analyzed equipment condition", report["equipment"]["equipment_id"], "ANALYZE")
        if feedback:
            append_feedback(OUT_DIR, report["equipment"]["equipment_id"], feedback)
        self.send_json({
            "report": report,
            "agentic": agentic,
            "work_order": work_order,
            "failure_cost_impact": failure_cost_impact,
            "financial_impact": failure_cost_impact,
            "alerts": build_alerts(),
        })

    def handle_demo(self) -> None:
        reports = run_demo(DATA_DIR, OUT_DIR)
        self.send_json({"reports": reports, "alerts": build_alerts()})

    def handle_feedback(self, payload: dict) -> None:
        equipment_id = str(payload.get("equipment_id", "")).strip()
        feedback = str(payload.get("feedback", "")).strip()
        if not equipment_id or not feedback:
            raise ValueError("Equipment and feedback are required.")
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        append_feedback(OUT_DIR, equipment_id, feedback)
        self.send_json({"ok": True})

    def handle_what_if(self, payload: dict) -> None:
        equipment_id = str(payload.get("equipment_id", "")).strip()
        overrides = payload.get("overrides", {})
        if not equipment_id:
            raise ValueError("Equipment is required.")
        if not isinstance(overrides, dict):
            raise ValueError("Overrides must be an object.")

        sources = load_sources(DATA_DIR)
        sensor_index = sources["sensors"].index[
            sources["sensors"].equipment_id == equipment_id
        ].tolist()
        if not sensor_index:
            raise ValueError("Unknown equipment.")

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
            "What-if maintenance scenario for "
            f"{equipment_id}. Evaluate risk, RUL, recommended action, and spare impact. "
            f"Changed metrics: {', '.join(changed_metrics) if changed_metrics else 'none'}."
        )
        report = create_report_from_sources(query, equipment_id, sources)
        failure_cost_impact = build_failure_cost_impact(report)
        self.send_json(
            {
                "report": report,
                "failure_cost_impact": failure_cost_impact,
                "financial_impact": failure_cost_impact,
                "alerts": build_alerts_from_sources(sources),
                "role_notifications": build_role_notifications(
                    build_alerts_from_sources(sources), sources["spares"]
                ),
            }
        )

    def handle_work_order(self, payload: dict) -> None:
        equipment_id = str(payload.get("equipment_id", "")).strip()
        query = str(payload.get("query", "")).strip()
        if not equipment_id:
            raise ValueError("Equipment is required.")
        if not query:
            query = f"Generate maintenance work order for {equipment_id} based on active alert."

        sources = load_sources(DATA_DIR)
        report = create_report_from_sources(query, equipment_id, sources)
        work_order = build_work_order(report, sources)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "work_order.json").write_text(
            json.dumps(work_order, indent=2), encoding="utf-8"
        )
        append_audit("maintenance_engineer", "generated work order", equipment_id, work_order["work_order_id"])
        self.send_json({"work_order": work_order})

    def handle_knowledge_search(self, payload: dict) -> None:
        query = str(payload.get("query", "")).strip()
        equipment_id = str(payload.get("equipment_id", "")).strip() or None
        if not query:
            raise ValueError("Search query is required.")
        sources = load_sources(DATA_DIR)
        evidence = retrieve_context(query, equipment_id, sources, top_n=8)
        self.send_json(
            {
                "results": [
                    {
                        "source": item.source,
                        "title": item.title,
                        "score": item.score,
                        "detail": item.detail,
                    }
                    for item in evidence
                ]
            }
        )

    def handle_ingest(self, payload: dict) -> None:
        input_type = str(payload.get("input_type", "")).strip()
        equipment_id = str(payload.get("equipment_id", "")).strip()
        content = str(payload.get("content", "")).strip()
        if not input_type or not equipment_id or not content:
            raise ValueError("Input type, equipment, and content are required.")

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        record = {
            "record_id": f"IN-{uuid.uuid4().hex[:8].upper()}",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "input_type": input_type,
            "equipment_id": equipment_id,
            "content": content,
            "status": "captured for reasoning and feedback loop",
        }
        with (OUT_DIR / "ingested_inputs.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
        append_audit("maintenance_engineer", f"ingested {input_type}", equipment_id, record["record_id"])
        self.send_json({"ingested": record, "knowledge_center": build_knowledge_sources()})

    def handle_chat(self, payload: dict) -> None:
        equipment_id = str(payload.get("equipment_id", "")).strip() or None
        message = str(payload.get("message", "")).strip()
        history = payload.get("history", [])
        if not message:
            raise ValueError("Message is required.")
        if not isinstance(history, list):
            history = []

        context_messages = [
            str(item.get("content", ""))
            for item in history[-4:]
            if isinstance(item, dict) and item.get("content")
        ]
        query = " ".join(context_messages + [message])
        sources = load_sources(DATA_DIR)
        report = create_report_from_sources(query, equipment_id, sources)
        response = build_chat_response(report)
        turn = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "equipment_id": report["equipment"]["equipment_id"],
            "user": message,
            "assistant": response,
            "risk_level": report["risk"]["level"],
        }
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        with (OUT_DIR / "conversation_log.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(turn) + "\n")
        append_audit("maintenance_engineer", "asked copilot follow-up", report["equipment"]["equipment_id"], "CHAT")
        self.send_json({"turn": turn, "report": report})

    def handle_operation_simulator(self, payload: dict) -> None:
        equipment_id = str(payload.get("equipment_id", "")).strip()
        strategy = str(payload.get("strategy", "restricted_operation")).strip()
        if not equipment_id:
            raise ValueError("Equipment is required.")
        result = simulate_operation_strategy(equipment_id, strategy)
        append_audit("production_supervisor", f"simulated {strategy}", equipment_id, "SIMULATION")
        self.send_json({"simulation": result})

    def handle_save_work_order(self, payload: dict) -> None:
        work_order = payload.get("work_order")
        if not isinstance(work_order, dict):
            raise ValueError("Work order is required.")
        status = str(payload.get("status", work_order.get("status", "Open"))).strip() or "Open"
        work_order["status"] = status
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        with (OUT_DIR / "saved_work_orders.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(work_order) + "\n")
        append_audit(
            "maintenance_planner",
            f"saved work order status {status}",
            str(work_order.get("equipment_id", "")),
            str(work_order.get("work_order_id", "")),
        )
        self.send_json({"saved": True, "work_order": work_order})

    def handle_plant_incident_demo(self) -> None:
        query = (
            "Plant incident demo: Down coiler mandrel expansion failed twice, "
            "tail-end slip is visible, and spare mandrel segment is unavailable. "
            "Run full autonomous investigation and prepare executive decision output."
        )
        agentic = run_agentic_analysis(query, "HRM-COIL-03")
        report = agentic["base_report"]
        sources = load_sources(DATA_DIR)
        work_order = build_work_order(report, sources)
        enterprise = build_enterprise_dashboard()
        append_audit("demo_operator", "ran plant incident demo", "HRM-COIL-03", work_order["work_order_id"])
        self.send_json(
            {
                "report": report,
                "agentic": agentic,
                "work_order": work_order,
                "enterprise": enterprise,
                "alerts": build_alerts(),
            }
        )

    def read_json(self) -> dict:
        length = int(self.headers.get("content-length", "0"))
        if length <= 0:
            return {}
        body = self.rfile.read(length).decode("utf-8")
        return json.loads(body)

    def serve_file(self, path: Path) -> None:
        if not path.is_file() or WEB_DIR not in path.resolve().parents and path.resolve() != WEB_DIR:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        content = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_pdf(self, filename: str, text: str) -> None:
        body = make_simple_pdf(text)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_download(self, filename: str, body: bytes, content_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_report_export(self, query_string: str) -> None:
        query = parse_qs(query_string)
        report_type = query.get("type", ["executive_summary"])[0]
        export_format = query.get("format", ["json"])[0]
        report_payload = build_enterprise_report(report_type)
        safe_type = report_type.replace(" ", "_").replace("-", "_")
        if export_format == "pdf":
            self.send_pdf(f"{safe_type}.pdf", report_payload["text"])
            return
        if export_format == "excel":
            body = report_payload["csv"].encode("utf-8")
            self.send_download(
                f"{safe_type}.xls",
                body,
                "application/vnd.ms-excel; charset=utf-8",
            )
            return
        body = json.dumps(report_payload["json"], indent=2).encode("utf-8")
        self.send_download(f"{safe_type}.json", body, "application/json; charset=utf-8")

    def log_message(self, format: str, *args: object) -> None:
        return


def build_bootstrap() -> dict:
    sources = load_sources(DATA_DIR)
    demo_queries = json.loads((DATA_DIR / "demo_queries.json").read_text(encoding="utf-8"))
    alerts = build_alerts_from_sources(sources)
    alert_map = {item["equipment_id"]: item for item in alerts}
    sensors = []
    for row in sources["sensors"].to_dict(orient="records"):
        alert = alert_map.get(row.get("equipment_id"), {})
        sensors.append(
            {
                **row,
                "risk_score": alert.get("risk_score"),
                "risk_level": alert.get("risk_level", "low"),
            }
        )
    spares = sources["spares"].to_dict(orient="records")
    history = sources["history"].to_dict(orient="records")
    return {
        "equipment": sensors,
        "spares": spares,
        "history": history,
        "demo_queries": demo_queries,
        "alerts": alerts,
        "role_definitions": ROLE_DEFINITIONS,
        "role_notifications": build_role_notifications(alerts, sources["spares"]),
        "live_monitor": build_live_monitor(),
        "intelligence": build_intelligence(),
        "knowledge_center": build_knowledge_sources(),
        "agent_metrics": build_default_agent_metrics(),
        "enterprise": build_enterprise_dashboard(),
        "brand": {"name": BRAND_NAME, "subtitle": BRAND_SUBTITLE},
        "equipment_master": normalized_enterprise_equipment(sources),
        "operations_center": build_operations_center(),
        "plant_command_center": build_plant_command_center(),
        "plant_digital_twin": build_plant_digital_twin(),
        "ai_pipeline": build_ai_pipeline_visibility(),
        "report_catalog": build_report_catalog(),
        "dependency_graph": build_dependency_graph(),
    }


def read_json_file(name: str, fallback):
    path = DATA_DIR / name
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def load_enterprise_equipment() -> list[dict]:
    return read_json_file("equipment.json", [])


def normalize_risk_level_from_score(score, fallback: str = "low") -> str:
    try:
        return classify_risk_score(float(score))
    except (TypeError, ValueError):
        fallback_value = str(fallback or "low").lower()
        return fallback_value if fallback_value in {"critical", "high", "medium", "low"} else "low"


def normalized_enterprise_equipment(sources: dict | None = None) -> list[dict]:
    equipment = load_enterprise_equipment()
    risk_rows = []
    if sources:
        risk_rows = rank_bottlenecks(sources, selected_id="")
    else:
        try:
            risk_rows = rank_bottlenecks(load_sources(DATA_DIR), selected_id="")
        except Exception:
            risk_rows = []
    risk_map = {row["equipment_id"]: row for row in risk_rows}
    normalized = []
    for asset in equipment:
        asset_id = asset.get("id") or asset.get("equipment_id")
        risk_row = risk_map.get(asset_id, {})
        fallback_score = max(0.0, min(100.0, 100.0 - float(asset.get("health_score", 75) or 75)))
        risk_score = float(risk_row.get("risk_score", asset.get("risk_score", fallback_score)))
        normalized.append(
            {
                **asset,
                "risk_score": round(risk_score, 1),
                "risk_level": normalize_risk_level_from_score(risk_score, asset.get("risk_level", "low")),
            }
        )
    return normalized


def load_enterprise_work_orders() -> list[dict]:
    return read_json_file("work_orders.json", [])


def load_enterprise_spares() -> list[dict]:
    return read_json_file("spare_parts.json", [])


def load_enterprise_failures() -> list[dict]:
    return read_json_file("failure_reports.json", [])


def load_enterprise_sensor_data() -> list[dict]:
    return read_json_file("sensor_data.json", [])


def load_enterprise_sensor_history() -> list[dict]:
    return read_json_file("sensor_data_full.json", [])


def load_enterprise_maintenance_logs() -> list[dict]:
    return read_json_file("maintenance_logs.json", [])


def load_enterprise_failure_modes() -> list[dict]:
    return read_json_file("failure_modes.json", [])


def risk_weight(level: str) -> int:
    return {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(str(level).lower(), 1)


def build_operations_center() -> dict:
    equipment = normalized_enterprise_equipment()
    work_orders = load_enterprise_work_orders()
    spares = load_enterprise_spares()
    failures = load_enterprise_failures()
    if not equipment:
        return {"kpis": [], "top_risks": []}
    critical = [item for item in equipment if item["risk_level"] == "critical"]
    high = [item for item in equipment if item["risk_level"] == "high"]
    open_work_orders = [item for item in work_orders if item.get("status") not in {"Completed", "Closed"}]
    spare_value = sum(int(item.get("estimated_cost_inr", 0)) * max(1, int(item.get("current_stock", 0))) for item in spares)
    avg_mtbf = round(sum(float(item["mtbf"]) for item in equipment) / len(equipment), 1)
    avg_mttr = round(sum(float(item["mttr"]) for item in equipment) / len(equipment), 1)
    availability = round(sum(float(item["health_score"]) for item in equipment) / len(equipment), 1)
    oee = round(max(64, availability - len(critical) * 1.8 - len(high) * 0.7), 1)
    production_risk = sum((100 - float(item["health_score"])) * risk_weight(item["risk_level"]) for item in equipment)
    maintenance_cost = sum(int(item.get("estimated_cost_inr", 0)) for item in open_work_orders)
    top_risks = sorted(equipment, key=lambda item: (risk_weight(item["risk_level"]), -float(item["health_score"])), reverse=True)[:8]
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "kpis": [
            {"label": "Plant Availability", "value": f"{availability}%", "help": "Plant-Level KPI - health-weighted plant availability"},
            {"label": "MTBF", "value": f"{avg_mtbf} h", "help": "Plant-Level KPI - enterprise equipment average"},
            {"label": "MTTR", "value": f"{avg_mttr} h", "help": "Plant-Level KPI - enterprise equipment average"},
            {"label": "OEE", "value": f"{oee}%", "help": "Plant-Level KPI - operations effectiveness estimate"},
            {"label": "Maintenance Cost", "value": maintenance_cost, "help": "Plant-Level KPI - open work order exposure INR", "money": True},
            {"label": "Spare Inventory Value", "value": spare_value, "help": "Plant-Level KPI - stores inventory value INR", "money": True},
            {"label": "Open Work Orders", "value": len(open_work_orders), "help": "Plant-Level KPI - non-closed work orders"},
            {"label": "Critical Assets", "value": len(critical), "help": "Plant-Level KPI - assets requiring immediate decision"},
            {"label": "Predicted Failures", "value": len([item for item in failures if item.get("severity") in {"critical", "high"}]), "help": "Plant-Level KPI - high-risk historical/predicted events"},
            {"label": "Production Risk Exposure", "value": int(production_risk * 11500), "help": "Plant-Level KPI - risk-weighted INR exposure", "money": True},
        ],
        "top_risks": top_risks,
    }


def build_plant_command_center() -> dict:
    sources = load_sources(DATA_DIR)
    equipment = normalized_enterprise_equipment(sources)
    sensors = load_enterprise_sensor_data()
    logs = load_enterprise_maintenance_logs()
    failures = load_enterprise_failures()
    work_orders = load_enterprise_work_orders()
    sensor_map = {item["equipment_id"]: item for item in sensors}
    total_assets = len(equipment)
    healthy = [item for item in equipment if item["risk_level"] == "low" and item["health_score"] >= 80]
    warning = [item for item in equipment if item["risk_level"] in {"medium", "high"}]
    critical = [item for item in equipment if item["risk_level"] == "critical"]
    active_alerts = [
        item for item in sensors
        if str(alert_from_sensor_record(item)).lower() not in {"normal_watch", "none", ""}
    ]
    open_wos = [item for item in work_orders if item.get("status") not in {"Completed", "Closed"}]
    weighted_health = round(
        sum(float(item["health_score"]) * risk_weight(item["criticality"]) for item in equipment)
        / max(1, sum(risk_weight(item["criticality"]) for item in equipment)),
        1,
    )
    sector_rows = build_sector_heatmap(equipment, sensors)
    risk_rows = []
    for item in equipment:
        sensor = sensor_map.get(item["id"], {})
        alert = alert_from_sensor_record(sensor)
        score = round((100 - float(item["health_score"])) * risk_weight(item["risk_level"]) + (12 if alert else 0), 1)
        risk_rows.append(
            {
                "id": item["id"],
                "name": item["name"],
                "area": item["area"],
                "health_score": item["health_score"],
                "active_alert": alert,
                "risk_level": item["risk_level"],
                "risk_score": score,
            }
        )
    return {
        "kpis": [
            {"label": "Total Assets", "value": total_assets},
            {"label": "Healthy Assets", "value": len(healthy)},
            {"label": "Warning Assets", "value": len(warning)},
            {"label": "Critical Assets", "value": len(critical)},
            {"label": "Active Alerts", "value": len(active_alerts)},
            {"label": "Open Work Orders", "value": len(open_wos)},
        ],
        "plant_health": {
            "score": weighted_health,
            "maintenance_required": len(warning) + len(critical),
            "distribution": {
                "healthy": len(healthy),
                "warning": len([item for item in equipment if item["risk_level"] == "medium"]),
                "high": len([item for item in equipment if item["risk_level"] == "high"]),
                "critical": len(critical),
            },
            "trend_7_days": [
                {"day": f"D-{6 - idx}", "score": round(max(10, min(99, weighted_health + math.sin(idx / 1.6) * 2.8 - (6 - idx) * 0.35)), 1)}
                for idx in range(7)
            ],
        },
        "sector_heatmap": sector_rows,
        "critical_assets": sorted(risk_rows, key=lambda item: item["risk_score"], reverse=True)[:10],
        "maintenance_feed": sorted(logs, key=lambda item: item.get("date", ""), reverse=True)[:12],
        "predictive_timeline": build_predictive_timeline(equipment, failures, work_orders),
    }


def alert_from_sensor_record(sensor: dict) -> str:
    if not sensor:
        return ""
    if "active_alert" in sensor:
        return str(sensor["active_alert"])
    if float(sensor.get("pressure", 999)) <= 95:
        return "HYD_PRESS_LOW"
    if float(sensor.get("oil_quality", 100)) <= 55:
        return "OIL_QUALITY_LOW"
    if float(sensor.get("temperature", 0)) >= 82:
        return "TEMP_HIGH"
    if float(sensor.get("vibration", 0)) >= 5.2:
        return "VIBRATION_HIGH"
    return "NORMAL_WATCH"


def build_sector_heatmap(equipment: list[dict], sensors: list[dict]) -> list[dict]:
    sectors = [
        ("Blast Furnace", "Blast Furnace"),
        ("Steel Melting Shop", "Steel Melting Shop"),
        ("Rolling Mill", "Rolling Mill"),
        ("Coke Oven", "Coke Oven"),
        ("Sinter Plant", "Sinter Plant"),
        ("Utility Plant", "Utilities"),
    ]
    sensor_map = {item["equipment_id"]: item for item in sensors}
    rows = []
    for label, area in sectors:
        assets = [item for item in equipment if item["area"] == area]
        alerts = [asset for asset in assets if alert_from_sensor_record(sensor_map.get(asset["id"], {})) != "NORMAL_WATCH"]
        health = round(sum(float(item["health_score"]) for item in assets) / max(1, len(assets)), 1)
        risk = max((item["risk_level"] for item in assets), key=risk_weight, default="low")
        rows.append(
            {
                "sector": label,
                "area": area,
                "health": health,
                "asset_count": len(assets),
                "active_alerts": len(alerts),
                "risk_level": risk,
            }
        )
    return rows


def build_predictive_timeline(equipment: list[dict], failures: list[dict], work_orders: list[dict]) -> list[dict]:
    now = datetime.now().replace(microsecond=0)
    windows = [("Today", 0), ("7 Days", 7), ("30 Days", 30), ("90 Days", 90)]
    rows = []
    for label, days in windows:
        cutoff = now + timedelta(days=days)
        candidates = [
            item for item in equipment
            if int(item.get("rul_hours", 9999)) <= max(24, days * 24 if days else 24)
        ]
        planned = [
            item for item in work_orders
            if item.get("status") in {"Open", "Assigned", "In Progress"}
        ][: max(2, len(candidates))]
        rows.append(
            {
                "window": label,
                "date": cutoff.date().isoformat(),
                "predicted_failures": [
                    {"asset": item["name"], "id": item["id"], "mode": (item.get("failure_modes") or ["failure risk"])[0]}
                    for item in candidates[:5]
                ],
                "planned_shutdowns": [
                    {"work_order": item["work_order_id"], "asset": item["asset_name"], "status": item["status"]}
                    for item in planned[:5]
                ],
                "maintenance_schedules": len(planned),
            }
        )
    return rows


def build_plant_digital_twin() -> dict:
    equipment = normalized_enterprise_equipment()
    work_orders = load_enterprise_work_orders()
    failures = load_enterprise_failures()
    maintenance_logs = load_enterprise_maintenance_logs()
    sensor_history = load_enterprise_sensor_history()
    sensor_rows = {item["equipment_id"]: item for item in load_enterprise_sensor_data()}
    zones = ["Blast Furnace", "Steel Melting Shop", "Rolling Mill", "Coke Oven", "Sinter Plant", "Utilities"]
    zone_positions = {
        "Blast Furnace": (18, 28),
        "Steel Melting Shop": (44, 24),
        "Rolling Mill": (72, 34),
        "Coke Oven": (18, 70),
        "Sinter Plant": (44, 72),
        "Utilities": (73, 72),
    }
    zone_payload = []
    for zone in zones:
        assets = [item for item in equipment if item["area"] == zone]
        base_x, base_y = zone_positions[zone]
        zone_payload.append(
            {
                "name": zone,
                "x": base_x,
                "y": base_y,
                "health_score": round(sum(item["health_score"] for item in assets) / max(1, len(assets)), 1),
                "risk_level": max((item["risk_level"] for item in assets), key=risk_weight, default="low"),
                "assets": [
                    build_twin_asset(
                        asset,
                        index,
                        base_x,
                        base_y,
                        work_orders,
                        failures,
                        sensor_rows,
                        maintenance_logs,
                        sensor_history,
                    )
                    for index, asset in enumerate(assets)
                ],
            }
        )
    return {"zones": zone_payload, "legend": {"green": "Healthy", "yellow": "Warning", "orange": "High Risk", "red": "Critical"}}


def build_twin_asset(
    asset: dict,
    index: int,
    base_x: int,
    base_y: int,
    work_orders: list[dict],
    failures: list[dict],
    sensor_rows: dict,
    maintenance_logs: list[dict] | None = None,
    sensor_history: list[dict] | None = None,
) -> dict:
    maintenance_logs = maintenance_logs or load_enterprise_maintenance_logs()
    sensor_history = sensor_history or load_enterprise_sensor_history()
    open_orders = [
        item for item in work_orders
        if item.get("equipment_id") == asset["id"] and item.get("status") not in {"Completed", "Closed"}
    ]
    asset_work_orders = [item for item in work_orders if item.get("equipment_id") == asset["id"]][:8]
    recent_failures = [item for item in failures if item.get("equipment_id") == asset["id"]][:8]
    maintenance_history = [item for item in maintenance_logs if item.get("equipment_id") == asset["id"]][:8]
    history = [item for item in sensor_history if item.get("equipment_id") == asset["id"]][-50:]
    return {
        **asset,
        "x": min(94, max(6, base_x + (index % 3 - 1) * 7)),
        "y": min(90, max(10, base_y + (index // 3) * 8)),
        "open_work_orders": len(open_orders),
        "recent_failures": recent_failures,
        "failure_reports": recent_failures,
        "maintenance_history": maintenance_history,
        "work_orders": asset_work_orders,
        "sensor_history": history,
        "sensor_snapshot": sensor_rows.get(asset["id"], {}),
    }


def build_dependency_graph() -> dict:
    equipment = normalized_enterprise_equipment()
    by_area = {}
    for asset in equipment:
        by_area.setdefault(asset["area"], []).append(asset)
    zone_chain = [
        "Coke Oven",
        "Sinter Plant",
        "Blast Furnace",
        "Steel Melting Shop",
        "Rolling Mill",
        "Utilities",
    ]
    nodes = [
        {
            "id": asset["id"],
            "name": asset["name"],
            "area": asset["area"],
            "risk_level": asset["risk_level"],
            "health_score": asset["health_score"],
            "production_impact": int((100 - asset["health_score"]) * risk_weight(asset["risk_level"]) * 1.8),
        }
        for asset in equipment
    ]
    edges = []
    for index, area in enumerate(zone_chain[:-1]):
        downstream_area = zone_chain[index + 1]
        for upstream in by_area.get(area, [])[:3]:
            for downstream in by_area.get(downstream_area, [])[:3]:
                edges.append(
                    {
                        "source": upstream["id"],
                        "target": downstream["id"],
                        "relationship": "process dependency",
                        "cascading_failure_risk": max(
                            risk_weight(upstream["risk_level"]),
                            risk_weight(downstream["risk_level"]),
                        )
                        * 18,
                    }
                )
    for utility in by_area.get("Utilities", [])[:4]:
        for area in ["Blast Furnace", "Steel Melting Shop", "Rolling Mill", "Sinter Plant"]:
            for target in by_area.get(area, [])[:1]:
                edges.append(
                    {
                        "source": utility["id"],
                        "target": target["id"],
                        "relationship": "utility support",
                        "cascading_failure_risk": risk_weight(utility["risk_level"]) * 16,
                    }
                )
    return {"nodes": nodes, "edges": edges}


def build_ai_pipeline_visibility() -> dict:
    now = datetime.now().replace(microsecond=0)
    stages = [
        ("Data Retrieval", 120),
        ("Knowledge Search", 340),
        ("Failure Analysis", 890),
        ("Root Cause Engine", 410),
        ("Maintenance Planning", 520),
        ("Report Generation", 360),
    ]
    elapsed = 0
    rows = []
    for name, base_latency in stages:
        latency = base_latency + (datetime.now().microsecond % 45)
        elapsed += latency
        rows.append(
            {
                "name": name,
                "status": "Completed",
                "latency_ms": latency,
                "completed_at": (now + timedelta(milliseconds=elapsed)).isoformat(timespec="milliseconds"),
            }
        )
    return {"stages": rows, "total_processing_ms": elapsed}


def build_report_catalog() -> list[dict]:
    return [
        {"id": "reliability_report", "name": "Reliability Report"},
        {"id": "maintenance_report", "name": "Maintenance Report"},
        {"id": "asset_health_report", "name": "Asset Health Report"},
        {"id": "executive_summary", "name": "Executive Summary"},
        {"id": "spare_consumption_report", "name": "Spare Consumption Report"},
        {"id": "failure_analysis_report", "name": "Failure Analysis Report"},
    ]


def build_alerts() -> list[dict]:
    sources = load_sources(DATA_DIR)
    return build_alerts_from_sources(sources)


def build_alerts_from_sources(sources: dict) -> list[dict]:
    rows = rank_bottlenecks(sources, selected_id="")
    return [
        {
            "equipment_id": row["equipment_id"],
            "equipment_name": row["equipment_name"],
            "risk_score": row["risk_score"],
            "risk_level": row["risk_level"],
        }
        for row in rows
    ]


def build_role_notifications(alerts: list[dict], spares) -> list[dict]:
    notifications = []
    for alert in alerts:
        level = alert["risk_level"]
        if level in {"critical", "high"}:
            notifications.append(
                {
                    "role": "Maintenance Engineer",
                    "equipment_id": alert["equipment_id"],
                    "message": (
                        f"{alert['equipment_name']} is {level}; inspect root cause "
                        "evidence and prepare corrective action."
                    ),
                    "priority": level,
                }
            )
        if level == "critical":
            notifications.append(
                {
                    "role": "Production Supervisor",
                    "equipment_id": alert["equipment_id"],
                    "message": (
                        f"{alert['equipment_name']} may affect line continuity; "
                        "review restricted operation or stop-window decision."
                    ),
                    "priority": "critical",
                }
            )

    for _, spare in spares.iterrows():
        if int(spare.available_qty) <= 0 or int(spare.lead_time_days) >= 14:
            notifications.append(
                {
                    "role": "Procurement Owner",
                    "equipment_id": spare.equipment_id,
                    "message": (
                        f"{spare.part} needs escalation: qty={int(spare.available_qty)}, "
                        f"lead time={int(spare.lead_time_days)} days."
                    ),
                    "priority": str(spare.criticality).lower(),
                }
            )
    return notifications


def build_live_monitor() -> dict:
    sources = load_sources(DATA_DIR)
    now = datetime.now().replace(microsecond=0)
    metrics = [
        "temperature_c",
        "vibration_mm_s",
        "motor_current_a",
        "hydraulic_pressure_bar",
    ]
    assets = []
    for idx, (_, row) in enumerate(sources["sensors"].iterrows(), start=1):
        points = []
        for step in range(12):
            timestamp = now - timedelta(minutes=(11 - step) * 5)
            point = {"timestamp": timestamp.isoformat(timespec="minutes")}
            for metric in metrics:
                base = float(row[metric])
                wave = math.sin(step / 1.7 + idx) * (0.025 * base)
                drift = (step - 6) * (0.004 * base) if metric != "hydraulic_pressure_bar" else -(step - 6) * (0.003 * base)
                point[metric] = round(base + wave + drift, 2)
            points.append(point)
        assets.append(
            {
                "equipment_id": row.equipment_id,
                "equipment_name": row.equipment_name,
                "active_alert": row.anomaly_alert,
                "points": points,
            }
        )
    return {"metrics": metrics, "assets": assets}


def build_intelligence() -> dict:
    sources = load_sources(DATA_DIR)
    alerts = build_alerts_from_sources(sources)
    return {
        "executive_summary": build_executive_summary(sources, alerts),
        "maintenance_plan": build_maintenance_plan(sources, alerts),
        "digital_twins": build_digital_twins(sources),
    }


def build_knowledge_sources() -> dict:
    return {
        "operational_failure_inputs": [
            source_summary("Equipment delay logs", DATA_DIR / "equipment_delay_logs.csv"),
            source_summary("Fault/error messages", DATA_DIR / "fault_messages.csv"),
            source_summary("Failure analysis reports", DATA_DIR / "failure_analysis_reports.md"),
            source_summary("Incident records and breakdown summaries", DATA_DIR / "incident_records.csv"),
        ],
        "condition_monitoring_inputs": [
            source_summary("Sensor data summaries", DATA_DIR / "sensor_snapshot.csv"),
            source_summary("Abnormality/anomaly alerts", DATA_DIR / "fault_messages.csv"),
            source_summary("Process condition indicators", DATA_DIR / "process_indicators.csv"),
        ],
        "knowledge_documentation_inputs": [
            source_summary("Equipment manuals", DATA_DIR / "equipment_manuals.md"),
            source_summary("Maintenance SOPs", DATA_DIR / "maintenance_sops.md"),
            source_summary("Historical maintenance records", DATA_DIR / "failure_history.csv"),
            source_summary("Spare parts and lead time", DATA_DIR / "spares_inventory.csv"),
        ],
        "user_interaction_inputs": [
            {"name": "Natural-language queries", "records": "live", "path": "/api/analyze"},
            {"name": "Scenario troubleshooting prompts", "records": "live", "path": "/api/what-if"},
            {"name": "Multi-turn conversation", "records": "live", "path": "/api/chat"},
        ],
        "ingested_runtime_inputs": read_jsonl_records(OUT_DIR / "ingested_inputs.jsonl"),
    }


def run_agentic_analysis(query: str, equipment_id: str | None) -> dict:
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    from services.agent_orchestrator import AgentOrchestrator

    orchestrator = AgentOrchestrator(DATA_DIR)
    return orchestrator.run(query, equipment_id)


def build_default_agent_metrics() -> dict:
    return {
        "agent_success_rate": 100,
        "average_diagnosis_confidence": 88,
        "knowledge_retrieval_accuracy": 91,
        "work_orders_generated": count_jsonl_rows(OUT_DIR / "conversation_log.jsonl") + 1,
        "historical_match_rate": 83,
    }


def count_jsonl_rows(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def build_enterprise_dashboard() -> dict:
    sources = load_sources(DATA_DIR)
    alerts = build_alerts_from_sources(sources)
    top_equipment = alerts[0]["equipment_id"] if alerts else "HRM-ROLL-01"
    top_report = create_report_from_sources(
        "Generate plant maintenance executive decision summary.", top_equipment, sources
    )
    return {
        "executive_decision_summary": build_executive_decision_summary(top_report, alerts),
        "incident_replay": build_incident_replay(top_report),
        "shift_handover": build_shift_handover(sources, alerts),
        "criticality_matrix": build_criticality_matrix(sources, alerts),
        "failure_cost_impact": build_failure_cost_impact(top_report),
        "budget_dashboard": build_budget_dashboard(),
        "root_cause_workspace": build_rca_workspace(top_report),
        "failure_prediction_timeline": build_failure_timeline(top_report),
        "operation_simulator": build_operation_options(top_report),
        "maintenance_kpis": build_maintenance_kpis(),
        "audit_trail": read_audit_trail(),
        "procurement_recommendations": build_procurement_recommendations(sources),
        "team_workload": build_team_workload(),
        "mobile_field_mode": build_mobile_field_mode(top_report),
        "executive_dashboard": build_management_dashboard(alerts),
    }


def build_incident_replay_payload(equipment_id: str | None = None) -> dict:
    sources = load_sources(DATA_DIR)
    if equipment_id:
        report = create_report_from_sources("Generate incident replay from historical failure records.", equipment_id, sources)
        records = [item for item in load_enterprise_failures() if item.get("equipment_id") == equipment_id]
        return {"incident_replay": build_incident_replay(report), "records": records}
    enterprise = build_enterprise_dashboard()
    return {"incident_replay": enterprise.get("incident_replay"), "records": load_enterprise_failures()[:12]}


def build_asset_context(equipment_id: str) -> dict:
    sources = load_sources(DATA_DIR)
    selected_id = equipment_id or str(sources["sensors"].iloc[0].equipment_id)
    brief = build_dynamic_investigation_brief(selected_id, sources)
    report = create_report_from_sources(brief, selected_id, sources)
    metrics = build_selected_asset_intelligence(selected_id, sources)
    report["prediction"].update(metrics["rul_model"])
    alerts = build_alerts_from_sources(sources)
    work_order = build_work_order(report, sources)
    return {
        "investigation_brief": brief,
        "report": report,
        "executive_decision_summary": build_executive_decision_summary(report, alerts, force_selected=True),
        "failure_cost_impact": build_failure_cost_impact(report),
        "work_order": work_order,
        "asset_intelligence": metrics,
    }


def build_selected_asset_intelligence(equipment_id: str, sources: dict) -> dict:
    equipment = next((item for item in normalized_enterprise_equipment(sources) if item["id"] == equipment_id), {})
    sensor = next((item for item in load_enterprise_sensor_data() if item["equipment_id"] == equipment_id), {})
    history = [item for item in load_enterprise_failures() if item["equipment_id"] == equipment_id]
    maintenance = [item for item in load_enterprise_maintenance_logs() if item["equipment_id"] == equipment_id]
    spares = [item for item in load_enterprise_spares() if item["equipment_id"] == equipment_id]
    work_orders = [item for item in load_enterprise_work_orders() if item["equipment_id"] == equipment_id]
    sensor_history = [item for item in load_enterprise_sensor_history() if item["equipment_id"] == equipment_id]
    row = sources["sensors"][sources["sensors"].equipment_id == equipment_id].iloc[0]
    breaches = condition_breaches(row)
    probability = calculate_failure_probability(equipment, sensor, history, maintenance, breaches, sensor_history)
    rul = calculate_dynamic_rul(equipment, probability, history, maintenance, breaches, sensor_history)
    return {
        "asset_profile": build_asset_profile(equipment, sensor, maintenance, history, work_orders, probability, rul),
        "failure_probability": probability,
        "rul_model": rul,
        "component_health": calculate_component_health(sensor, equipment),
        "maintenance_calendar": build_maintenance_calendar(equipment, history, maintenance, work_orders, rul),
        "spare_recommendations": build_spare_recommendations(equipment, spares, probability),
        "failure_timeline": build_asset_failure_timeline(probability, sensor_history),
        "relationship_view": build_asset_relationship_view(equipment),
        "source_counts": {
            "sensor_history": len(sensor_history),
            "failure_reports": len(history),
            "maintenance_logs": len(maintenance),
            "spare_parts": len(spares),
            "work_orders": len(work_orders),
        },
    }


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def trend_slope(rows: list[dict], metric: str) -> float:
    values = [float(item.get(metric, 0) or 0) for item in rows[-20:]]
    if len(values) < 2:
        return 0.0
    return (sum(values[-5:]) / min(5, len(values)) - sum(values[:5]) / min(5, len(values))) / max(1, len(values))


def calculate_failure_probability(
    equipment: dict,
    sensor: dict,
    history: list[dict],
    maintenance: list[dict],
    breaches: list,
    sensor_history: list[dict],
) -> dict:
    health = float(equipment.get("health_score", 75) or 75)
    severity_score = sum(SEVERITY_SCORE.get(str(item.get("severity", "medium")).lower(), 2) for item in history[:8])
    anomaly_score = len(breaches) * 8.5
    trend_risk = max(0, trend_slope(sensor_history, "vibration") * 18) + max(0, -trend_slope(sensor_history, "pressure") * 1.4)
    maintenance_gap = 12 if not maintenance else min(18, max(0, (datetime.now().date() - datetime.fromisoformat(maintenance[0]["date"]).date()).days / 12))
    probability = clamp((100 - health) * 0.62 + severity_score * 1.8 + anomaly_score + trend_risk + maintenance_gap, 4, 97)
    level = "low" if probability < 30 else "medium" if probability < 70 else "high"
    confidence = int(clamp(62 + len(sensor_history) * 0.3 + len(history) * 1.2 + len(maintenance) * 0.7, 58, 96))
    return {
        "percent": round(probability, 1),
        "level": level,
        "confidence": confidence,
        "drivers": {
            "health_score": health,
            "sensor_anomalies": len(breaches),
            "failure_history_records": len(history),
            "maintenance_records": len(maintenance),
            "trend_risk": round(trend_risk, 1),
        },
    }


def calculate_dynamic_rul(
    equipment: dict,
    probability: dict,
    history: list[dict],
    maintenance: list[dict],
    breaches: list,
    sensor_history: list[dict],
) -> dict:
    rated = float(equipment.get("rated_hours", 50000) or 50000)
    running = float(equipment.get("running_hours", rated - float(equipment.get("rul_hours", 600))) or 0)
    health = float(equipment.get("health_score", 75) or 75)
    base = max(0, (rated - running) * (health / 100))
    history_penalty = min(0.45, len(history) * 0.018)
    anomaly_penalty = min(0.35, len(breaches) * 0.07)
    trend_penalty = min(0.25, max(0, trend_slope(sensor_history, "vibration")) * 0.18)
    probability_penalty = float(probability["percent"]) / 250
    rul_hours = int(max(0, base * (1 - history_penalty - anomaly_penalty - trend_penalty - probability_penalty)))
    confidence = int(clamp(probability["confidence"] - len(breaches) * 2 + len(maintenance), 45, 96))
    confidence_label = "Low confidence" if confidence < 60 else "Medium confidence" if confidence < 80 else "High confidence"
    return {
        "estimated_remaining_useful_life_hours": rul_hours,
        "rul_hours": rul_hours,
        "rul_days": round(rul_hours / 24, 1),
        "rul_confidence": confidence,
        "rul_confidence_label": confidence_label,
        "rul_label": "Immediate intervention" if rul_hours <= 0 else f"{rul_hours} hours",
        "rul_explanation": "Dynamic RUL from health score, operating hours, anomalies, history, maintenance, and trend slope.",
    }


def calculate_component_health(sensor: dict, equipment: dict) -> dict:
    def high(value: float, warn: float, trip: float) -> int:
        return int(clamp(100 - max(0, (value - warn) / max(1, trip - warn)) * 72, 18, 100))

    def low(value: float, warn: float, trip: float) -> int:
        return int(clamp(100 - max(0, (warn - value) / max(1, warn - trip)) * 72, 18, 100))

    oil = low(float(sensor.get("oil_quality", 80) or 80), 62, 38)
    return {
        "mechanical": min(high(float(sensor.get("vibration", 2) or 2), 4.5, 7.1), oil),
        "electrical": high(float(sensor.get("current", 180) or 180), 340, 430),
        "hydraulic": low(float(sensor.get("pressure", 125) or 125), 112, 82),
        "thermal": high(float(sensor.get("temperature", 60) or 60), 78, 96),
        "process": int((low(float(sensor.get("flow", 150) or 150), 100, 70) + oil) / 2),
    }


def build_asset_profile(
    equipment: dict,
    sensor: dict,
    maintenance: list[dict],
    history: list[dict],
    work_orders: list[dict],
    probability: dict,
    rul: dict,
) -> dict:
    manufacturers = ["Tata Steel OEM Cell", "SMS Group", "Danieli", "ABB Industrial", "Siemens Industry"]
    manufacturer = manufacturers[abs(hash(equipment.get("id", ""))) % len(manufacturers)]
    commission_year = 2012 + abs(hash(equipment.get("name", ""))) % 9
    return {
        "asset_id": equipment.get("id"),
        "asset_name": equipment.get("name"),
        "area": equipment.get("area"),
        "sector": equipment.get("area"),
        "manufacturer": manufacturer,
        "commission_date": f"{commission_year}-04-01",
        "operating_hours": equipment.get("running_hours"),
        "criticality": equipment.get("criticality"),
        "current_failure_mode": (equipment.get("failure_modes") or [sensor.get("failure_signal", "watch")])[0],
        "failure_probability": probability["percent"],
        "rul_hours": rul["rul_hours"],
        "health_score": equipment.get("health_score"),
        "last_maintenance_date": maintenance[0]["date"] if maintenance else equipment.get("last_maintenance"),
        "next_planned_maintenance": next((item.get("created_at") for item in work_orders if item.get("status") in {"Open", "Assigned"}), "Not scheduled"),
        "asset_icon": equipment.get("type", "Industrial Asset"),
    }


def build_maintenance_calendar(equipment: dict, history: list[dict], maintenance: list[dict], work_orders: list[dict], rul: dict) -> list[dict]:
    return [
        {"window": "Today", "items": [f"Inspect {equipment.get('name')} if RUL below 48h", f"{len([w for w in work_orders if w.get('status') == 'Open'])} open work order(s)"]},
        {"window": "7 Days", "items": [f"Upcoming inspection based on {rul['rul_hours']}h RUL", f"{len(history[:5])} recent failure reference(s)"]},
        {"window": "30 Days", "items": [f"Planned PM after {maintenance[0]['action'] if maintenance else 'condition review'}", "Spare min-max review"]},
        {"window": "90 Days", "items": ["Reliability review", "Long-term component replacement planning"]},
    ]


def build_spare_recommendations(equipment: dict, spares: list[dict], probability: dict) -> list[dict]:
    ranked = sorted(spares, key=lambda item: (int(item.get("current_stock", 0)), -int(item.get("lead_time_days", 0))))
    return [
        {
            "part": item.get("part_name"),
            "quantity": max(1, int(item.get("min_stock", 1)) - int(item.get("current_stock", 0)) + 1),
            "stock": int(item.get("current_stock", 0)),
            "lead_time_days": int(item.get("lead_time_days", 0)),
            "availability": "In Stock" if int(item.get("current_stock", 0)) > 0 else "Stockout",
            "risk_if_unavailable": "High" if probability["percent"] >= 70 or int(item.get("lead_time_days", 0)) >= 14 else "Medium",
        }
        for item in ranked[:4]
    ]


def build_asset_failure_timeline(probability: dict, sensor_history: list[dict]) -> list[dict]:
    percent = float(probability["percent"])
    current = "Normal" if percent < 20 else "Watch" if percent < 45 else "Warning" if percent < 70 else "Critical"
    return [
        {"stage": "Normal", "active": current == "Normal"},
        {"stage": "Watch", "active": current == "Watch"},
        {"stage": "Warning", "active": current == "Warning"},
        {"stage": "Critical", "active": current == "Critical"},
        {"stage": "Predicted Failure", "active": percent >= 88},
    ]


def build_asset_relationship_view(equipment: dict) -> dict:
    type_name = str(equipment.get("type", "Asset"))
    mapping = {
        "Hydraulic System": ["Motor", "Pump", "Pressure Valve", "Hydraulic Tank", "Controller"],
        "Gearbox": ["Motor", "Coupling", "Bearings", "Lubrication System"],
        "Drive Motor": ["Rotor", "Stator", "Cooling Fan", "Drive Coupling", "Protection Relay"],
        "Steam Turbine": ["Rotor", "Governor Valve", "Bearings", "Steam Seal", "Oil System"],
        "Conveyor System": ["Drive Pulley", "Belt", "Idlers", "Tracking Switch", "Motor"],
    }
    children = mapping.get(type_name, ["Drive", "Bearings", "Controller", "Sensor Package"])
    return {"root": equipment.get("name"), "children": [{"name": item, "status": "linked"} for item in children]}


def build_dynamic_investigation_brief(equipment_id: str, sources: dict) -> str:
    sensors = sources["sensors"]
    row = sensors[sensors.equipment_id == equipment_id].iloc[0]
    breaches = condition_breaches(row)
    history = sources["history"][sources["history"].equipment_id == equipment_id].head(3)
    breach_text = ", ".join(
        f"{breach.metric}={breach.value} ({breach.level}, limit {breach.limit})"
        for breach in breaches
    ) or "no active threshold breach"
    history_text = ", ".join(
        f"{item.record_id}: {item.root_cause}" for _, item in history.iterrows()
    ) or "no prior failure match"
    profile = next((item for item in normalized_enterprise_equipment(sources) if item["id"] == equipment_id), {})
    failure_modes = ", ".join(profile.get("failure_modes", [])[:3]) or str(row.anomaly_alert)
    return (
        f"Investigate {row.equipment_name} ({equipment_id}) in {profile.get('area', 'plant area')}. "
        f"Active alert: {row.anomaly_alert}. Sensor anomalies: {breach_text}. "
        f"Known asset failure modes: {failure_modes}. Historical failures: {history_text}. "
        "Generate asset-specific diagnosis, RUL, business impact, root cause, maintenance action, and spare strategy."
    )


def build_executive_decision_summary(report: dict, alerts: list[dict], force_selected: bool = False) -> dict:
    risk = report["risk"]["level"]
    score = report["risk"]["score"]
    equipment = report["equipment"]
    impact = asset_impact_factors(equipment["equipment_id"])
    hours = impact["downtime_hours"][risk]
    cost_avoided = int(impact["repair_cost_inr"] * (1.55 if risk == "critical" else 1.25 if risk == "high" else 0.85))
    strategy = (
        "Controlled shutdown and immediate corrective work"
        if risk == "critical"
        else "Restricted operation with planned inspection window"
        if risk == "high"
        else "Continue operation with enhanced monitoring"
    )
    top = {
        "equipment_id": equipment["equipment_id"],
        "equipment_name": equipment["equipment_name"],
        "risk_level": risk,
    } if force_selected else alerts[0] if alerts else {
        "equipment_id": equipment["equipment_id"],
        "equipment_name": equipment["equipment_name"],
        "risk_level": risk,
    }
    return {
        "current_top_plant_risk": f"{top['equipment_name']} - {str(top['risk_level']).title()}",
        "asset": top["equipment_id"],
        "expected_production_impact": f"{int(hours * impact['production_tph'])} tonnes at risk / {hours} h exposure",
        "recommended_maintenance_strategy": strategy,
        "estimated_downtime_avoided": f"{max(1, hours - 1)} h",
        "estimated_cost_avoided_inr": cost_avoided + int(float(score) * 3500),
        "required_approvals": ["Maintenance Lead", "Production Supervisor", "Safety Officer"],
    }


def build_incident_replay(report: dict) -> dict:
    equipment = report["equipment"]
    fault = report["diagnosis"]["probable_fault"]
    causes = report["diagnosis"]["probable_root_causes"] or ["Field confirmation pending"]
    return {
        "incident_name": f"{equipment['equipment_name']} - {fault}",
        "risk_level": report["risk"]["level"],
        "timeline": [
            {"time": "09:10", "event": "Pressure dropped below stable operating band"},
            {"time": "09:25", "event": "Vibration trend increased above normal baseline"},
            {"time": "09:40", "event": f"PLC warning generated for {equipment['active_alert']}"},
            {"time": "10:05", "event": "Production impact detected through line-speed restriction"},
            {"time": "10:20", "event": "Failure mode confirmed for maintenance intervention"},
        ],
        "failure_progression": f"{fault} progressed from abnormal condition to production constraint.",
        "production_impact": "Reduced mill throughput and elevated unplanned downtime exposure",
        "corrective_actions_taken": [
            "Restricted operation until physical inspection was completed",
            "Validated sensor reading locally and reviewed historian trend",
            f"Inspected likely root cause: {causes[0]}",
            "Prepared work order and spare escalation path",
        ],
        "lessons_learned": [
            "Escalate recurring abnormal trends before trip-level condition is reached",
            "Link spare availability to maintenance priority before planning stop window",
            "Use historical failures and SOP evidence during shift handover",
        ],
    }


def build_shift_handover(sources: dict, alerts: list[dict]) -> dict:
    critical_alerts = [alert for alert in alerts if alert["risk_level"] == "critical"]
    spares = sources["spares"]
    shortage_rows = spares[(spares.available_qty <= 0) | (spares.lead_time_days >= 14)]
    notes = [
        "Verify abnormal readings locally at the start of next shift.",
        "Keep production supervisor informed before line-speed changes.",
        "Record inspection outcome and actual root cause in digital log.",
    ]
    summary = (
        f"{len(critical_alerts)} critical asset(s) remain open. "
        f"Top risk is {alerts[0]['equipment_name'] if alerts else 'none'}. "
        f"{len(shortage_rows)} spare issue(s) require procurement follow-up. "
        "Next shift should monitor trend stability and close pending inspection actions."
    )
    return {
        "shift": "B Shift to C Shift",
        "open_critical_alerts": critical_alerts,
        "work_completed": [
            "Initial condition review completed",
            "Historical failure match checked",
            "Spare availability reviewed",
        ],
        "completed_jobs": [
            {"job": "PLC fault-message triage", "owner": "Shift Reliability Engineer", "status": "completed"},
            {"job": "Critical spare inventory check", "owner": "Stores Controller", "status": "completed"},
        ],
        "pending_actions": [
            "Physical inspection of highest-risk equipment",
            "Supervisor approval for stop-window if trend worsens",
        ],
        "pending_jobs": [
            {"job": "Mandrel segment inspection", "owner": "Mechanical Maintenance", "status": "pending"},
            {"job": "Controlled stop-window decision", "owner": "Production Supervisor", "status": "pending"},
        ],
        "spare_shortages": [
            {
                "equipment_id": row.equipment_id,
                "part": row.part,
                "available_qty": int(row.available_qty),
                "lead_time_days": int(row.lead_time_days),
            }
            for _, row in shortage_rows.iterrows()
        ],
        "safety_observations": [
            "Hydraulic isolation required for pressure-related jobs",
            "Line restriction required before critical inspection",
        ],
        "next_shift_recommendations": [
            "Continue trend monitoring on critical assets every 30 minutes",
            "Confirm spare escalation status before approving stop-window plan",
            "Keep production supervisor aligned on restriction or shutdown decision",
        ],
        "shift_notes": notes,
        "summary": summary,
    }


def build_criticality_matrix(sources: dict, alerts: list[dict]) -> list[dict]:
    alert_map = {alert["equipment_id"]: alert for alert in alerts}
    rows = []
    for _, sensor in sources["sensors"].iterrows():
        alert = alert_map.get(sensor.equipment_id, {"risk_score": 40, "risk_level": "medium"})
        production = 95 if "COIL" in sensor.equipment_id else 88 if "ROLL" in sensor.equipment_id else 76
        safety = 92 if alert["risk_level"] == "critical" else 78 if alert["risk_level"] == "high" else 55
        cost = 86 if "COIL" in sensor.equipment_id else 74 if "FURN" in sensor.equipment_id else 68
        score = round(production * 0.4 + safety * 0.35 + cost * 0.25)
        rows.append(
            {
                "equipment_id": sensor.equipment_id,
                "equipment_name": sensor.equipment_name,
                "production_impact": production,
                "safety_impact": safety,
                "maintenance_cost": cost,
                "criticality_score": score,
                "criticality": "Critical" if score >= 85 else "High" if score >= 70 else "Medium",
            }
        )
    return sorted(rows, key=lambda item: item["criticality_score"], reverse=True)


def build_failure_cost_impact(report: dict) -> dict:
    risk = report["risk"]["level"]
    impact = asset_impact_factors(report["equipment"]["equipment_id"])
    hours = impact["downtime_hours"][risk]
    production_loss = int(hours * impact["production_tph"] * impact["tonne_value_inr"])
    repair_cost = int(impact["repair_cost_inr"] * (1.2 if risk == "critical" else 1.0 if risk == "high" else 0.72))
    downtime_cost = int(hours * impact["hourly_downtime_cost_inr"])
    spare_count = len(report.get("spares", []))
    inventory_cost = 90000 + spare_count * 25000 if risk in {"critical", "high"} else 30000
    failure_event_consequence = production_loss + repair_cost + downtime_cost
    business_exposure = failure_event_consequence + inventory_cost + int(production_loss * 0.18)
    controlled_shutdown_cost = int(max(120000, downtime_cost * 0.38 + repair_cost * 0.28))
    expected_savings = max(0, failure_event_consequence - controlled_shutdown_cost)
    roi_percent = round((expected_savings / controlled_shutdown_cost) * 100, 1) if controlled_shutdown_cost else 0.0
    return {
        "equipment_id": report["equipment"]["equipment_id"],
        "estimated_downtime_hours": hours,
        "production_loss_inr": production_loss,
        "repair_cost_inr": repair_cost,
        "downtime_cost_inr": downtime_cost,
        "inventory_cost_inr": inventory_cost,
        "total_business_impact_inr": production_loss + repair_cost,
        "total_risk_exposure_inr": business_exposure,
        "business_exposure_inr": business_exposure,
        "failure_event_consequence_inr": failure_event_consequence,
        "potential_failure_cost_inr": failure_event_consequence,
        "controlled_shutdown_cost_inr": controlled_shutdown_cost,
        "shutdown_cost_inr": controlled_shutdown_cost,
        "expected_savings_inr": expected_savings,
        "roi_percent": roi_percent,
        "scenario_comparison": [
            {"scenario": "Run to failure", "risk_exposure_inr": business_exposure + 520000, "downtime_hours": hours + 5},
            {"scenario": "Restricted operation", "risk_exposure_inr": max(0, business_exposure - 330000), "downtime_hours": max(1, hours - 2)},
            {"scenario": "Planned stop", "risk_exposure_inr": max(0, business_exposure - 460000), "downtime_hours": max(1, hours - 3)},
        ],
    }


def asset_impact_factors(equipment_id: str) -> dict:
    equipment = next((item for item in normalized_enterprise_equipment() if item["id"] == equipment_id), {})
    production_tph = int(equipment.get("production_tph", 90) or 90)
    repair_cost = int(equipment.get("base_repair_cost_inr", 220000) or 220000)
    criticality = str(equipment.get("criticality", "high")).lower()
    criticality_multiplier = 1.35 if criticality == "critical" else 1.1 if criticality == "high" else 0.82
    return {
        "production_tph": production_tph,
        "repair_cost_inr": repair_cost,
        "tonne_value_inr": 14500 if "Rolling" in str(equipment.get("area", "")) else 11800,
        "hourly_downtime_cost_inr": int(production_tph * 9800 * criticality_multiplier),
        "downtime_hours": {
            "critical": 8 if production_tph >= 130 else 6,
            "high": 5 if production_tph >= 100 else 4,
            "medium": 3,
            "low": 1,
        },
    }


def build_budget_dashboard() -> dict:
    return {
        "monthly_maintenance_spend_inr": 4200000,
        "emergency_repairs_inr": 1350000,
        "planned_maintenance_inr": 2100000,
        "cost_avoidance_inr": 1850000,
        "inventory_value_inr": 7600000,
        "trend": [
            {"month": "Jan", "spend": 31, "emergency": 9, "planned": 17},
            {"month": "Feb", "spend": 34, "emergency": 11, "planned": 18},
            {"month": "Mar", "spend": 38, "emergency": 13, "planned": 19},
            {"month": "Apr", "spend": 36, "emergency": 10, "planned": 20},
            {"month": "May", "spend": 41, "emergency": 14, "planned": 21},
            {"month": "Jun", "spend": 42, "emergency": 13.5, "planned": 21},
        ],
    }


def build_rca_workspace(report: dict) -> dict:
    causes = report["diagnosis"]["probable_root_causes"] or ["Condition abnormality requires inspection"]
    primary = causes[0]
    return {
        "problem": f"{report['equipment']['equipment_name']} - {report['diagnosis']['probable_fault']}",
        "five_why": [
            {"why": 1, "answer": f"Asset generated {report['diagnosis']['probable_fault']} alert."},
            {"why": 2, "answer": "Condition data breached operating threshold."},
            {"why": 3, "answer": f"Historical pattern points to {primary}."},
            {"why": 4, "answer": "Inspection or spare readiness has not fully removed the failure mode."},
            {"why": 5, "answer": "Preventive action and procurement escalation are required."},
        ],
        "fishbone": {
            "Man": "Shift handover and inspection closure need verification.",
            "Machine": primary,
            "Material": "Spare availability may delay recovery.",
            "Method": "Follow SOP and controlled stop-window decision.",
            "Measurement": "Validate sensor reading locally before restart.",
            "Environment": "High-duty hot rolling campaign increases degradation rate.",
        },
        "probable_rca": primary,
    }


def build_failure_timeline(report: dict) -> list[dict]:
    fault = report["diagnosis"]["probable_fault"]
    return [
        {"period": "Today", "event": f"{fault} detected", "impact": "Inspection required"},
        {"period": "+7 Days", "event": "Component degradation accelerates", "impact": "Quality and stability risk rises"},
        {"period": "+14 Days", "event": "Process defects become visible", "impact": "Rework or coil rejection likely"},
        {"period": "+21 Days", "event": "Unplanned shutdown risk", "impact": "High production loss exposure"},
    ]


def build_operation_options(report: dict) -> list[dict]:
    return [
        simulate_operation_strategy(report["equipment"]["equipment_id"], "continue_running"),
        simulate_operation_strategy(report["equipment"]["equipment_id"], "restricted_operation"),
        simulate_operation_strategy(report["equipment"]["equipment_id"], "planned_shutdown"),
        simulate_operation_strategy(report["equipment"]["equipment_id"], "emergency_shutdown"),
    ]


def simulate_operation_strategy(equipment_id: str, strategy: str) -> dict:
    matrix = {
        "continue_running": ("Critical", 94, 980000, 0, "No immediate loss, high breakdown exposure", "Not recommended except under controlled temporary production approval."),
        "restricted_operation": ("High", 62, 420000, 2, "Reduced throughput, lower failure exposure", "Recommended as a short-term bridge while preparing inspection."),
        "planned_shutdown": ("Medium", 34, 610000, 4, "Controlled downtime and safer repair window", "Preferred option for critical assets with spare blockers."),
        "emergency_shutdown": ("Low", 18, 1250000, 6, "Immediate production stop, lowest asset risk", "Use if trip conditions or safety risk continue."),
    }
    risk, score, cost, downtime, impact, recommendation = matrix.get(strategy, matrix["restricted_operation"])
    return {
        "equipment_id": equipment_id,
        "strategy": strategy.replace("_", " ").title(),
        "risk": risk,
        "risk_score": score,
        "estimated_cost_inr": cost,
        "downtime_hours": downtime,
        "production_impact": impact,
        "recommendation": recommendation,
    }


def build_maintenance_kpis() -> dict:
    return {
        "mtbf_hours": 428,
        "mttr_hours": 5.6,
        "availability_percent": 96.8,
        "oee_impact_percent": 2.4,
        "breakdown_frequency": 7,
        "maintenance_compliance_percent": 91,
        "work_order_completion_rate_percent": 84,
        "emergency_repair_ratio_percent": 22,
        "preventive_maintenance_success_percent": 89,
        "planned_vs_unplanned_ratio": "68:32",
        "trend": [
            {"week": "W1", "availability": 95.9, "mttr": 6.4},
            {"week": "W2", "availability": 96.2, "mttr": 6.1},
            {"week": "W3", "availability": 96.4, "mttr": 5.9},
            {"week": "W4", "availability": 96.8, "mttr": 5.6},
        ],
    }


def append_audit(user: str, action: str, equipment_id: str, decision: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "user": user,
        "action": action,
        "equipment_id": equipment_id,
        "decision": decision,
    }
    with (OUT_DIR / "audit_trail.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


def read_audit_trail() -> list[dict]:
    rows = read_jsonl_records(OUT_DIR / "audit_trail.jsonl")
    if rows:
        return rows[-12:]
    return [
        {
            "timestamp": "2026-06-07T10:31:00",
            "user": "maintenance_engineer",
            "action": "approved work order",
            "equipment_id": "HRM-ROLL-01",
            "decision": "WO-231",
        },
        {
            "timestamp": "2026-06-07T10:35:00",
            "user": "production_supervisor",
            "action": "acknowledged alert",
            "equipment_id": "HRM-COIL-03",
            "decision": "restricted operation",
        },
    ]


def build_procurement_recommendations(sources: dict) -> list[dict]:
    rows = sources["spares"][
        (sources["spares"].available_qty <= 0) | (sources["spares"].lead_time_days >= 14)
    ]
    recommendations = []
    for _, row in rows.iterrows():
        suggested = 10 if row.criticality == "critical" else 6 if row.criticality == "high" else 3
        recommendations.append(
            {
                "equipment_id": row.equipment_id,
                "part": row.part,
                "current_qty": int(row.available_qty),
                "lead_time_days": int(row.lead_time_days),
                "suggested_order_qty": suggested,
                "risk_if_delayed": f"{str(row.criticality).title()} production impact",
            }
        )
    return recommendations


def build_team_workload() -> list[dict]:
    return [
        {"engineer": "A. Sharma", "assigned_tasks": 5, "open_work_orders": 3, "critical_jobs": 2, "completion_rate": 86},
        {"engineer": "R. Iyer", "assigned_tasks": 4, "open_work_orders": 2, "critical_jobs": 1, "completion_rate": 91},
        {"engineer": "S. Khan", "assigned_tasks": 6, "open_work_orders": 4, "critical_jobs": 2, "completion_rate": 78},
        {"engineer": "P. Verma", "assigned_tasks": 3, "open_work_orders": 1, "critical_jobs": 0, "completion_rate": 94},
    ]


def build_mobile_field_mode(report: dict) -> dict:
    return {
        "equipment_qr": report["equipment"]["equipment_id"],
        "field_actions": [
            "Scan equipment QR",
            "View current diagnosis and safety classification",
            "Upload inspection photo",
            "Record measurement confirmation",
            "Close work order after supervisor approval",
        ],
        "active_work_order_status": "inspection pending",
    }


def build_management_dashboard(alerts: list[dict]) -> dict:
    critical = sum(1 for item in alerts if item["risk_level"] == "critical")
    high = sum(1 for item in alerts if item["risk_level"] == "high")
    top = alerts[0] if alerts else {}
    readiness = max(0, 100 - critical * 18 - high * 9)
    risk_exposure = 2450000 + critical * 650000 + high * 300000
    downtime = 9.5 + critical * 2.5
    return {
        "plant_health_score": readiness,
        "critical_assets": critical,
        "predicted_failures": critical + high,
        "risk_exposure_inr": risk_exposure,
        "budget_impact_inr": 1350000,
        "downtime_exposure_hours": downtime,
        "maintenance_readiness_percent": readiness,
        "spare_risks": critical + high + 2,
        "monthly_cost_impact_inr": 1350000 + critical * 240000,
        "top_bottleneck": top.get("equipment_id", "None"),
        "executive_summary": (
            f"Plant risk is concentrated in {top.get('equipment_name', 'the monitored hot rolling assets')}. "
            f"{critical} critical and {high} high-risk asset(s) create about INR {risk_exposure:,} exposure "
            f"and {downtime:.1f} h downtime exposure unless planned maintenance is executed."
        ),
    }


def source_summary(name: str, path: Path) -> dict:
    if not path.exists():
        return {"name": name, "records": 0, "path": str(path.relative_to(ROOT_DIR)), "status": "missing"}
    if path.suffix.lower() == ".csv":
        records = len(read_csv_records(path))
    else:
        text = path.read_text(encoding="utf-8")
        records = max(1, text.count("## "))
    return {
        "name": name,
        "records": records,
        "path": str(path.relative_to(ROOT_DIR)),
        "status": "available",
    }


def read_csv_records(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_jsonl_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows[-20:]


def build_chat_response(report: dict) -> str:
    causes = "; ".join(report["diagnosis"]["probable_root_causes"])
    first_action = report["recommendations"][0] if report["recommendations"] else "Escalate to maintenance review."
    modes = report["diagnosis"].get("asset_failure_modes", [])
    mode_text = ", ".join(item.get("failure_mode", "") for item in modes[:3]) or report["diagnosis"]["probable_fault"]
    parts = [
        row for row in load_enterprise_spares()
        if row.get("equipment_id") == report["equipment"]["equipment_id"]
    ][:3]
    spare_text = ", ".join(
        f"{item['part_name']} stock {item['current_stock']} lead {item['lead_time_days']}d"
        for item in parts
    ) or "no asset-specific spare record"
    return (
        f"{report['equipment']['equipment_id']} {report['equipment']['equipment_name']} "
        f"({report['equipment'].get('type', 'asset')}, {report['equipment'].get('area', 'plant')}) "
        f"is classified as {report['risk']['level']} with urgency {report['priority']['urgency']}. "
        f"Asset failure modes reviewed: {mode_text}. Probable fault: "
        f"{report['diagnosis']['probable_fault']}. Likely root cause: {causes}. "
        f"Spare context: {spare_text}. "
        f"First action: {first_action}"
    )


def build_executive_summary(sources: dict, alerts: list[dict]) -> dict:
    critical_count = sum(1 for alert in alerts if alert["risk_level"] == "critical")
    high_count = sum(1 for alert in alerts if alert["risk_level"] == "high")
    spare_blockers = sources["spares"][
        (sources["spares"].available_qty <= 0) | (sources["spares"].lead_time_days >= 14)
    ]
    risk_scores = [float(alert["risk_score"]) for alert in alerts]
    readiness_score = max(0, round(100 - sum(risk_scores) / max(len(risk_scores), 1) * 0.72 - len(spare_blockers) * 2, 1))
    downtime_exposure_minutes = int(round(sum(score * 3.8 for score in risk_scores)))
    return {
        "asset_count": len(sources["sensors"]),
        "critical_assets": critical_count,
        "high_assets": high_count,
        "spare_blockers": len(spare_blockers),
        "readiness_score": readiness_score,
        "downtime_exposure_minutes": downtime_exposure_minutes,
        "top_bottleneck": alerts[0] if alerts else None,
    }


def build_maintenance_plan(sources: dict, alerts: list[dict]) -> list[dict]:
    plan = []
    start = datetime.now().replace(second=0, microsecond=0) + timedelta(hours=2)
    for index, alert in enumerate(alerts):
        equipment_id = alert["equipment_id"]
        spares = sources["spares"][sources["spares"].equipment_id == equipment_id]
        blockers = spares[(spares.available_qty <= 0) | (spares.lead_time_days >= 14)]
        duration = int(60 + float(alert["risk_score"]) * 2.2)
        priority = index + 1
        window_start = start + timedelta(hours=index * 4)
        plan.append(
            {
                "priority": priority,
                "equipment_id": equipment_id,
                "equipment_name": alert["equipment_name"],
                "risk_level": alert["risk_level"],
                "risk_score": alert["risk_score"],
                "recommended_window": window_start.isoformat(timespec="minutes"),
                "estimated_duration_minutes": duration,
                "status": "blocked by spares" if not blockers.empty else "ready to schedule",
                "required_spares": [
                    {
                        "part": row.part,
                        "available_qty": int(row.available_qty),
                        "lead_time_days": int(row.lead_time_days),
                    }
                    for _, row in blockers.iterrows()
                ],
            }
        )
    return plan


def build_digital_twins(sources: dict) -> list[dict]:
    twins = []
    for _, row in sources["sensors"].iterrows():
        component_scores = {
            "thermal": health_from_high(float(row.temperature_c), warn=75, trip=90),
            "mechanical": health_from_high(float(row.vibration_mm_s), warn=4.5, trip=7.1),
            "electrical": health_from_high(float(row.motor_current_a), warn=320, trip=380),
            "hydraulic": health_from_low(float(row.hydraulic_pressure_bar), warn=120, trip=95),
            "process": health_from_high(float(row.roll_gap_variation_mm), warn=0.25, trip=0.4),
        }
        health = round(sum(component_scores.values()) / len(component_scores), 1)
        twins.append(
            {
                "equipment_id": row.equipment_id,
                "equipment_name": row.equipment_name,
                "overall_health": health,
                "active_alert": row.anomaly_alert,
                "components": component_scores,
                "degradation_stage": degradation_stage(health),
            }
        )
    return twins


def health_from_high(value: float, warn: float, trip: float) -> float:
    if value <= warn:
        return 100.0
    if value >= trip:
        return 25.0
    return round(100 - ((value - warn) / (trip - warn)) * 55, 1)


def health_from_low(value: float, warn: float, trip: float) -> float:
    if value >= warn:
        return 100.0
    if value <= trip:
        return 25.0
    return round(100 - ((warn - value) / (warn - trip)) * 55, 1)


def degradation_stage(health: float) -> str:
    if health < 40:
        return "failure risk"
    if health < 65:
        return "degraded"
    if health < 82:
        return "watch"
    return "stable"


def build_work_order(report: dict, sources: dict) -> dict:
    equipment_id = report["equipment"]["equipment_id"]
    spares = sources["spares"][sources["spares"].equipment_id == equipment_id]
    risk_level = report["risk"]["level"]
    required_spares = [
        {
            "part": row.part,
            "available_qty": int(row.available_qty),
            "lead_time_days": int(row.lead_time_days),
            "criticality": row.criticality,
        }
        for _, row in spares.iterrows()
        if int(row.available_qty) <= 0 or int(row.lead_time_days) >= 14
    ]
    now = datetime.now().replace(microsecond=0)
    duration = 240 if risk_level == "critical" else 180 if risk_level == "high" else 120
    estimated_manpower = 5 if risk_level == "critical" else 4 if risk_level == "high" else 2
    shutdown_hours = 6 if risk_level == "critical" else 4 if risk_level == "high" else 2
    estimated_cost = 145000 if risk_level == "critical" else 85000 if risk_level == "high" else 35000
    recommendation_text = " ".join(report["recommendations"]).lower()
    required_skills = ["mechanical inspection", "maintenance safety"]
    if "hydraulic" in recommendation_text or "pressure" in recommendation_text:
        required_skills.append("hydraulic troubleshooting")
    if "vibration" in recommendation_text or "bearing" in recommendation_text:
        required_skills.append("vibration analysis")
    if required_spares:
        required_skills.append("spare planning")
    root_cause = report["diagnosis"]["probable_root_causes"][0] if report["diagnosis"]["probable_root_causes"] else "Pending field confirmation"
    required_parts = [
        {
            "part": row.part,
            "available_qty": int(row.available_qty),
            "lead_time_days": int(row.lead_time_days),
            "criticality": row.criticality,
        }
        for _, row in spares.iterrows()
    ]
    return {
        "work_order_id": f"WO-{now.strftime('%Y')}-{now.strftime('%H%M')}",
        "created_at": now.isoformat(timespec="minutes"),
        "equipment_id": equipment_id,
        "equipment_name": report["equipment"]["equipment_name"],
        "asset": equipment_id,
        "priority": f"P1 {risk_level.title()}" if risk_level == "critical" else f"P2 {risk_level.title()}",
        "problem": report["diagnosis"]["probable_fault"],
        "root_cause": root_cause,
        "status": "Open",
        "lifecycle": ["Open", "Assigned", "In Progress", "Completed", "Closed"],
        "estimated_duration_minutes": duration,
        "estimated_manpower": estimated_manpower,
        "estimated_cost_inr": estimated_cost,
        "required_skills": list(dict.fromkeys(required_skills)),
        "required_parts": required_parts,
        "shutdown_duration_hours": shutdown_hours,
        "safety_permit": "Required" if risk_level in {"critical", "high"} else "Not required",
        "safety_classification": "high energy isolation" if risk_level in {"critical", "high"} else "standard maintenance",
        "assigned_team": "Mechanical Maintenance",
        "owner_role": "Maintenance Engineer",
        "approval_role": "Production Supervisor" if risk_level in {"critical", "high"} else "Maintenance Lead",
        "safety_steps": [
            "Confirm line restriction or stop-window approval.",
            "Apply lockout/tagout for the affected equipment drive and hydraulic circuit.",
            "Verify zero stored energy before inspection.",
        ],
        "tasks": [
            {"sequence": idx, "task": task}
            for idx, task in enumerate(report["recommendations"], start=1)
        ],
        "required_spares": required_spares,
        "acceptance_criteria": [
            "No active trip-level threshold remains after restart.",
            "Vibration, pressure, and current trends remain inside warning limits for 30 minutes.",
            "Engineer feedback and actual root cause are recorded in the digital log.",
        ],
    }


def build_work_order_pdf_text() -> str:
    work_order_path = OUT_DIR / "work_order.json"
    if work_order_path.exists():
        work_order = json.loads(work_order_path.read_text(encoding="utf-8"))
    else:
        sources = load_sources(DATA_DIR)
        alerts = build_alerts_from_sources(sources)
        equipment_id = alerts[0]["equipment_id"] if alerts else "HRM-ROLL-01"
        report = create_report_from_sources("Generate enterprise work order.", equipment_id, sources)
        work_order = build_work_order(report, sources)

    lines = [
        f"{BRAND_NAME} Enterprise Work Order",
        BRAND_SUBTITLE,
        "",
        f"Work Order: {work_order.get('work_order_id', '-')}",
        f"Status: {work_order.get('status', 'Open')}",
        f"Asset: {work_order.get('equipment_id', '-')} - {work_order.get('equipment_name', '-')}",
        f"Priority: {work_order.get('priority', '-')}",
        f"Problem: {work_order.get('problem', '-')}",
        f"Root Cause: {work_order.get('root_cause', '-')}",
        f"Assigned Team: {work_order.get('assigned_team', '-')}",
        f"Manpower: {work_order.get('estimated_manpower', '-')}",
        f"Estimated Cost INR: {work_order.get('estimated_cost_inr', '-')}",
        f"Shutdown Duration: {work_order.get('shutdown_duration_hours', '-')} h",
        f"Safety Permit: {work_order.get('safety_permit', '-')}",
        "",
        "Tasks:",
    ]
    for task in work_order.get("tasks", [])[:8]:
        lines.append(f"{task.get('sequence', '-')}. {task.get('task', '-')}")
    lines.append("")
    lines.append("Required Parts:")
    for part in work_order.get("required_parts", [])[:8]:
        lines.append(
            f"- {part.get('part', '-')} | qty {part.get('available_qty', '-')} | lead {part.get('lead_time_days', '-')} days"
        )
    lines.append("")
    lines.append("Acceptance Criteria:")
    for item in work_order.get("acceptance_criteria", [])[:5]:
        lines.append(f"- {item}")
    return "\n".join(lines)


def build_shift_handover_pdf_text() -> str:
    data = build_shift_handover(load_sources(DATA_DIR), build_alerts())
    lines = [
        f"{BRAND_NAME} Shift Handover Report",
        BRAND_SUBTITLE,
        "",
        f"Shift: {data['shift']}",
        data["summary"],
        "",
        "Open Alerts:",
    ]
    for alert in data["open_critical_alerts"][:8]:
        lines.append(f"- {alert['equipment_id']} {alert['equipment_name']} risk {alert['risk_level']} score {alert['risk_score']}")
    lines.append("")
    lines.append("Completed Jobs:")
    for job in data.get("completed_jobs", []):
        lines.append(f"- {job['job']} | {job['owner']} | {job['status']}")
    lines.append("")
    lines.append("Pending Jobs:")
    for job in data.get("pending_jobs", []):
        lines.append(f"- {job['job']} | {job['owner']} | {job['status']}")
    lines.append("")
    lines.append("Spare Risks:")
    for spare in data["spare_shortages"][:8]:
        lines.append(f"- {spare['equipment_id']} {spare['part']} qty {spare['available_qty']} lead {spare['lead_time_days']} days")
    lines.append("")
    lines.append("Safety Notes:")
    for note in data["safety_observations"]:
        lines.append(f"- {note}")
    lines.append("")
    lines.append("Next Shift Recommendations:")
    for note in data.get("next_shift_recommendations", []):
        lines.append(f"- {note}")
    return "\n".join(lines)


def build_executive_report_pdf_text() -> str:
    sources = load_sources(DATA_DIR)
    alerts = build_alerts_from_sources(sources)
    top_equipment = alerts[0]["equipment_id"] if alerts else "HRM-ROLL-01"
    report = create_report_from_sources("Generate executive maintenance report.", top_equipment, sources)
    work_order = build_work_order(report, sources)
    decision = build_executive_decision_summary(report, alerts)
    impact = build_failure_cost_impact(report)
    evidence = report.get("traceability", [])
    lines = [
        f"{BRAND_NAME} Executive Maintenance Report",
        BRAND_SUBTITLE,
        "",
        "Executive Summary",
        f"{decision['current_top_plant_risk']} requires {decision['recommended_maintenance_strategy']}.",
        f"Expected production impact: {decision['expected_production_impact']}.",
        f"Estimated downtime avoided: {decision['estimated_downtime_avoided']}. Estimated cost avoided INR {decision['estimated_cost_avoided_inr']}.",
        "",
        "Asset Information",
        f"{report['equipment']['equipment_id']} - {report['equipment']['equipment_name']} - Alert {report['equipment']['active_alert']}",
        "",
        "Diagnosis",
        f"{report['diagnosis']['probable_fault']} / Risk {report['risk']['level']} / Score {report['risk']['score']}",
        "",
        "Root Cause Analysis",
        ", ".join(report["diagnosis"]["probable_root_causes"] or ["Pending field confirmation"]),
        "",
        "Evidence Used",
    ]
    for item in evidence[:5]:
        lines.append(f"- {item['source']}: {item['title']}")
    lines.extend(
        [
            "",
            "Business Impact",
            f"Production loss INR {impact['production_loss_inr']} / Repair cost INR {impact['repair_cost_inr']} / Total risk exposure INR {impact['total_risk_exposure_inr']}",
            "",
            "Risk Assessment",
            f"Condition {report['risk']['drivers']['condition_score']} / History {report['risk']['drivers']['historical_severity_score']} / Spares {report['risk']['drivers']['spares_penalty']}",
            "",
            "Maintenance Plan",
        ]
    )
    for item in report["recommendations"][:6]:
        lines.append(f"- {item}")
    lines.extend(["", "Required Spares"])
    for part in work_order.get("required_parts", [])[:6]:
        lines.append(f"- {part['part']} / stock {part['available_qty']} / lead {part['lead_time_days']} days")
    lines.extend(
        [
            "",
            "Work Order Summary",
            f"{work_order['work_order_id']} / {work_order['priority']} / {work_order['assigned_team']} / {work_order['shutdown_duration_hours']} h shutdown",
            "",
            "Approval Requirements",
            ", ".join(decision["required_approvals"]),
        ]
    )
    return "\n".join(lines)


def build_enterprise_report(report_type: str) -> dict:
    operations = build_operations_center()
    equipment = load_enterprise_equipment()
    failures = load_enterprise_failures()
    spares = load_enterprise_spares()
    work_orders = load_enterprise_work_orders()
    report_name = next(
        (item["name"] for item in build_report_catalog() if item["id"] == report_type),
        report_type.replace("_", " ").title(),
    )
    rows = []
    if report_type == "reliability_report":
        rows = [
            {
                "equipment_id": item["id"],
                "asset": item["name"],
                "area": item["area"],
                "health_score": item["health_score"],
                "mtbf": item["mtbf"],
                "mttr": item["mttr"],
                "rul_hours": item["rul_hours"],
                "risk_level": item["risk_level"],
            }
            for item in equipment
        ]
    elif report_type == "maintenance_report":
        rows = [
            {
                "work_order_id": item["work_order_id"],
                "equipment_id": item["equipment_id"],
                "asset": item["asset_name"],
                "priority": item["priority"],
                "status": item["status"],
                "team": item["assigned_team"],
                "estimated_cost_inr": item["estimated_cost_inr"],
            }
            for item in work_orders
        ]
    elif report_type == "asset_health_report":
        rows = [
            {
                "equipment_id": item["id"],
                "asset": item["name"],
                "area": item["area"],
                "type": item["type"],
                "criticality": item["criticality"],
                "health_score": item["health_score"],
                "status": item["status"],
            }
            for item in equipment
        ]
    elif report_type == "spare_consumption_report":
        rows = [
            {
                "part_id": item["part_id"],
                "equipment_id": item["equipment_id"],
                "asset": item["asset_name"],
                "part": item["part_name"],
                "stock": item["current_stock"],
                "lead_time_days": item["lead_time_days"],
                "estimated_cost_inr": item["estimated_cost_inr"],
                "vendor": item["preferred_vendor"],
            }
            for item in spares
        ]
    elif report_type == "failure_analysis_report":
        rows = [
            {
                "record_id": item["record_id"],
                "equipment_id": item["equipment_id"],
                "asset": item["asset_name"],
                "failure_mode": item["failure_mode"],
                "severity": item["severity"],
                "downtime_minutes": item["downtime_minutes"],
                "root_cause": item["root_cause"],
            }
            for item in failures
        ]
    else:
        rows = [
            {"metric": item["label"], "value": item["value"], "description": item["help"]}
            for item in operations.get("kpis", [])
        ]
    json_payload = {
        "platform": BRAND_NAME,
        "subtitle": BRAND_SUBTITLE,
        "report": report_name,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": (
            f"{report_name} generated for Tata Steel maintenance leadership. "
            f"Current enterprise view contains {len(equipment)} assets, "
            f"{len(work_orders)} work orders, {len(failures)} failure records, and {len(spares)} spare records."
        ),
        "operations_center": operations,
        "rows": rows,
    }
    text_lines = [
        f"{BRAND_NAME} - {report_name}",
        BRAND_SUBTITLE,
        "",
        json_payload["summary"],
        "",
        "Executive Metrics",
    ]
    for item in operations.get("kpis", [])[:10]:
        text_lines.append(f"- {item['label']}: {item['value']} ({item['help']})")
    text_lines.extend(["", "Report Rows"])
    for row in rows[:24]:
        text_lines.append("- " + " | ".join(f"{key}: {value}" for key, value in row.items()))
    csv_lines = ["Report," + report_name, "Platform," + BRAND_NAME, ""]
    if rows:
        headers = list(rows[0].keys())
        csv_lines.append(",".join(headers))
        for row in rows:
            csv_lines.append(",".join(csv_escape(row.get(header, "")) for header in headers))
    return {"json": json_payload, "text": "\n".join(text_lines), "csv": "\n".join(csv_lines)}


def csv_escape(value: object) -> str:
    text = str(value).replace('"', '""')
    if any(char in text for char in [",", "\n", '"']):
        return f'"{text}"'
    return text


def make_simple_pdf(text: str) -> bytes:
    lines = [line[:105] for line in text.splitlines()[:48]]
    content_lines = ["BT", "/F1 10 Tf", "50 790 Td", "14 TL"]
    for line in lines:
        safe = pdf_escape(line)
        content_lines.append(f"({safe}) Tj")
        content_lines.append("T*")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    return bytes(pdf)


def pdf_escape(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def main() -> None:
    parser = argparse.ArgumentParser(description=f"{BRAND_NAME} frontend server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()
    host = args.host
    port = args.port
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log_file = OUT_DIR / "web_server.log"
    try:
        server = ThreadingHTTPServer((host, port), MaintenanceWizardHandler)
        message = f"{BRAND_NAME} frontend running at http://{host}:{port}"
        log_file.write_text(message + "\n", encoding="utf-8")
        print(message, flush=True)
        server.serve_forever()
    except Exception as exc:
        log_file.write_text(f"Server failed: {exc}\n", encoding="utf-8")
        raise


if __name__ == "__main__":
    main()
