from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from backend.utils.numpy_compat import apply_numpy_compat

apply_numpy_compat()
import pandas as pd


LIMITS = {
    "temperature_c": {"warn": 75.0, "trip": 90.0, "direction": "high"},
    "vibration_mm_s": {"warn": 4.5, "trip": 7.1, "direction": "high"},
    "motor_current_a": {"warn": 320.0, "trip": 380.0, "direction": "high"},
    "oil_pressure_bar": {"warn": 2.8, "trip": 2.0, "direction": "low"},
    "hydraulic_pressure_bar": {"warn": 120.0, "trip": 95.0, "direction": "low"},
    "roll_gap_variation_mm": {"warn": 0.25, "trip": 0.4, "direction": "high"},
}

SERVICE_INTERVAL_HOURS = {
    "HRM-ROLL-01": 1800,
    "HRM-FURN-02": 1600,
    "HRM-COIL-03": 1900,
}

SEVERITY_SCORE = {"low": 1, "medium": 2, "high": 3, "critical": 4}
RISK_LABELS = [(90, "critical"), (75, "high"), (50, "medium"), (0, "low")]


def ensure_columns(frame: pd.DataFrame, defaults: Dict[str, object]) -> pd.DataFrame:
    """Return a copy with generated/dashboard columns present for Pandas 3.x-safe access."""
    safe = frame.copy()
    for column, default in defaults.items():
        if column not in safe.columns:
            safe[column] = default
    return safe


def prepare_spares_frame(spares: pd.DataFrame) -> pd.DataFrame:
    safe = ensure_columns(
        spares,
        {
            "equipment_id": "",
            "available_qty": 0,
            "lead_time_days": 0,
            "criticality": "low",
            "part": "unlisted spare",
            "_criticality_score": 0,
        },
    )
    safe["available_qty"] = pd.to_numeric(safe["available_qty"], errors="coerce").fillna(0)
    safe["lead_time_days"] = pd.to_numeric(safe["lead_time_days"], errors="coerce").fillna(0)
    safe["criticality"] = safe["criticality"].fillna("low").astype(str).str.lower()
    safe["_criticality_score"] = safe["criticality"].map(SEVERITY_SCORE).fillna(0)
    return safe


@dataclass
class Evidence:
    source: str
    title: str
    score: float
    detail: str


@dataclass
class Breach:
    metric: str
    value: float
    level: str
    limit: float


def tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9_]+", text.lower()) if len(token) > 2}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_sources(data_dir: Path) -> dict:
    sources = {
        "manuals": read_text(data_dir / "equipment_manuals.md"),
        "sops": read_text(data_dir / "maintenance_sops.md"),
        "history": pd.read_csv(data_dir / "failure_history.csv"),
        "sensors": pd.read_csv(data_dir / "sensor_snapshot.csv"),
        "spares": pd.read_csv(data_dir / "spares_inventory.csv"),
    }
    equipment_path = data_dir / "equipment.json"
    failure_modes_path = data_dir / "failure_modes.json"
    sources["equipment_master"] = json.loads(equipment_path.read_text(encoding="utf-8")) if equipment_path.exists() else []
    sources["failure_modes"] = json.loads(failure_modes_path.read_text(encoding="utf-8")) if failure_modes_path.exists() else []
    sources["spares"] = prepare_spares_frame(sources["spares"])
    return sources


def equipment_profile(equipment_id: str, sources: dict) -> dict:
    for item in sources.get("equipment_master", []):
        if item.get("id") == equipment_id:
            return item
    return {}


def asset_failure_modes(equipment_id: str, sources: dict) -> List[dict]:
    return [
        item for item in sources.get("failure_modes", [])
        if item.get("equipment_id") == equipment_id
    ]


def split_markdown_sections(source_name: str, text: str) -> List[Evidence]:
    sections: List[Evidence] = []
    current_title = source_name
    current_lines: List[str] = []

    for line in text.splitlines():
        if line.startswith("## "):
            if current_lines:
                sections.append(
                    Evidence(source_name, current_title, 0.0, "\n".join(current_lines).strip())
                )
            current_title = line.replace("## ", "").strip()
            current_lines = []
        elif line.startswith("# "):
            current_title = line.replace("# ", "").strip()
        else:
            current_lines.append(line)

    if current_lines:
        sections.append(Evidence(source_name, current_title, 0.0, "\n".join(current_lines).strip()))
    return sections


def retrieve_context(query: str, equipment_id: Optional[str], sources: dict, top_n: int = 5) -> List[Evidence]:
    query_tokens = tokenize(query)
    if equipment_id:
        query_tokens.add(equipment_id.lower())

    candidates: List[Evidence] = []
    candidates.extend(split_markdown_sections("equipment_manuals", sources["manuals"]))
    candidates.extend(split_markdown_sections("maintenance_sops", sources["sops"]))

    history = sources["history"]
    if equipment_id:
        history = history[history.equipment_id == equipment_id]
    for _, row in history.iterrows():
        detail = (
            f"{row.equipment_id} {row.equipment_name} {row.component}: "
            f"{row.fault_message}. Symptoms: {row.symptoms}. "
            f"Root cause: {row.root_cause}. Action: {row.action_taken}."
        )
        candidates.append(Evidence("failure_history", row.record_id, 0.0, detail))

    scored: List[Evidence] = []
    equipment_ids = set(str(value) for value in sources["sensors"].equipment_id)
    for item in candidates:
        item_text = f"{item.title} {item.detail}"
        if equipment_id:
            mentions_other_equipment = any(
                candidate_id != equipment_id and candidate_id in item_text for candidate_id in equipment_ids
            )
            if mentions_other_equipment and equipment_id not in item_text:
                continue
        item_tokens = tokenize(item_text)
        overlap = len(query_tokens & item_tokens)
        equipment_boost = 4 if equipment_id and equipment_id.lower() in item.detail.lower() else 0
        score = overlap + equipment_boost
        if score > 0:
            scored.append(Evidence(item.source, item.title, float(score), item.detail))

    return sorted(scored, key=lambda item: item.score, reverse=True)[:top_n]


def select_equipment(query: str, equipment_id: Optional[str], sources: dict) -> str:
    sensors = sources["sensors"]
    if equipment_id:
        return equipment_id

    lowered = query.lower()
    for _, row in sensors.iterrows():
        if row.equipment_id.lower() in lowered or row.equipment_name.lower() in lowered:
            return row.equipment_id

    tokens = tokenize(query)
    best_id = sensors.iloc[0].equipment_id
    best_score = -1
    for _, row in sensors.iterrows():
        score = len(tokens & tokenize(f"{row.equipment_id} {row.equipment_name} {row.anomaly_alert}"))
        if score > best_score:
            best_id = row.equipment_id
            best_score = score
    return best_id


def condition_breaches(sensor_row: pd.Series) -> List[Breach]:
    breaches: List[Breach] = []
    for metric, limits in LIMITS.items():
        value = float(sensor_row[metric])
        direction = limits["direction"]
        warn = limits["warn"]
        trip = limits["trip"]
        level = ""
        limit = warn

        if direction == "high":
            if value >= trip:
                level, limit = "trip", trip
            elif value >= warn:
                level, limit = "warn", warn
        else:
            if value <= trip:
                level, limit = "trip", trip
            elif value <= warn:
                level, limit = "warn", warn

        if level:
            breaches.append(Breach(metric, value, level, float(limit)))
    return breaches


def anomaly_score(breaches: Sequence[Breach]) -> float:
    score = 0.0
    for breach in breaches:
        score += 22.0 if breach.level == "trip" else 12.0
    return min(score, 100.0)


def estimate_rul(equipment_id: str, sensor_row: pd.Series, breaches: Sequence[Breach]) -> dict:
    interval = SERVICE_INTERVAL_HOURS.get(equipment_id, 1800)
    used = float(sensor_row.operating_hours_since_service)
    age_factor = min(1.0, used / interval)
    condition_penalty = anomaly_score(breaches) / 100.0
    health_index = max(0.0, 100.0 * (1.0 - age_factor) - 55.0 * condition_penalty)
    remaining_hours = max(0, int(round((health_index / 100.0) * interval)))
    if remaining_hours == 0:
        rul_label = "Immediate intervention"
        rul_explanation = "Current service age and active condition breaches have exhausted the safe operating window."
    elif remaining_hours < 24:
        rul_label = "Less than 24 hours"
        rul_explanation = "Schedule intervention within the current operating day."
    else:
        rul_label = f"{remaining_hours} hours"
        rul_explanation = "Estimated remaining useful life from service age and condition penalties."

    return {
        "method": "service interval adjusted by current condition breaches",
        "service_interval_hours": interval,
        "operating_hours_since_service": int(used),
        "health_index": round(health_index, 1),
        "estimated_remaining_useful_life_hours": remaining_hours,
        "rul_label": rul_label,
        "rul_explanation": rul_explanation,
    }


def estimate_rul_with_profile(
    equipment_id: str,
    sensor_row: pd.Series,
    breaches: Sequence[Breach],
    profile: dict,
) -> dict:
    result = estimate_rul(equipment_id, sensor_row, breaches)
    if not profile:
        return result
    profile_rul = int(profile.get("rul_hours", result["estimated_remaining_useful_life_hours"]) or 0)
    condition_rul = int(result["estimated_remaining_useful_life_hours"])
    blended = max(0, min(profile_rul, condition_rul if condition_rul else profile_rul))
    result["estimated_remaining_useful_life_hours"] = blended
    result["rul_label"] = "Immediate intervention" if blended == 0 else f"{blended} hours"
    result["health_index"] = min(float(profile.get("health_score", result["health_index"])), result["health_index"])
    result["method"] = "asset digital twin RUL blended with current condition breaches"
    result["rul_explanation"] = (
        f"Uses {profile.get('name', equipment_id)} digital twin health, rated hours, "
        "active sensor anomalies, and asset-specific failure history."
    )
    return result


def risk_level(score: float) -> str:
    for threshold, label in RISK_LABELS:
        if score >= threshold:
            return label
    return "low"


def assess_risk(
    equipment_id: str,
    breaches: Sequence[Breach],
    history_matches: pd.DataFrame,
    spares: pd.DataFrame,
) -> dict:
    condition = anomaly_score(breaches)
    severity = 0.0
    if not history_matches.empty:
        severity = max(SEVERITY_SCORE.get(str(value).lower(), 1) for value in history_matches.severity)
    spares_penalty = 0.0
    related_spares = spares[spares.equipment_id == equipment_id]
    if not related_spares.empty:
        unavailable = related_spares[related_spares.available_qty <= 0]
        long_lead = related_spares[related_spares.lead_time_days >= 14]
        spares_penalty = min(25.0, len(unavailable) * 8.0 + len(long_lead) * 5.0)

    risk_score = min(100.0, condition * 0.55 + severity * 12.0 + spares_penalty)
    return {
        "score": round(risk_score, 1),
        "level": risk_level(risk_score),
        "drivers": {
            "condition_score": round(condition, 1),
            "historical_severity_score": severity,
            "spares_penalty": round(spares_penalty, 1),
        },
    }


def matched_history(equipment_id: str, query: str, history: pd.DataFrame) -> pd.DataFrame:
    tokens = tokenize(query)
    rows = []
    for _, row in history[history.equipment_id == equipment_id].iterrows():
        text = f"{row.fault_message} {row.symptoms} {row.root_cause} {row.action_taken}"
        score = len(tokens & tokenize(text))
        rows.append((score, row))

    if not rows:
        return history.iloc[0:0]

    ranked = sorted(rows, key=lambda item: item[0], reverse=True)
    positive = [row for score, row in ranked if score > 0]
    if not positive:
        positive = [ranked[0][1]]
    return pd.DataFrame(positive[:3])


def build_recommendations(
    equipment_id: str,
    sensor_row: pd.Series,
    breaches: Sequence[Breach],
    history_matches: pd.DataFrame,
    spares: pd.DataFrame,
    risk: dict,
    failure_modes: Sequence[dict] | None = None,
) -> List[str]:
    recommendations: List[str] = []
    breach_metrics = {breach.metric for breach in breaches}
    failure_modes = list(failure_modes or [])
    primary_mode = failure_modes[0] if failure_modes else {}
    spares = prepare_spares_frame(spares)

    if risk["level"] in {"critical", "high"}:
        recommendations.append(
            f"Move {sensor_row.equipment_name} to restricted operation and prepare a controlled stop window."
        )
    if primary_mode:
        recommendations.append(
            f"Investigate {primary_mode.get('failure_mode')} caused by {primary_mode.get('likely_root_cause')}; "
            f"execute: {primary_mode.get('recommended_action')}."
        )
    if "vibration_mm_s" in breach_metrics:
        equipment_text = f"{sensor_row.equipment_name} {sensor_row.anomaly_alert}".lower()
        if "gearbox" in equipment_text:
            recommendations.append("Inspect gear mesh, bearing race condition, coupling alignment, and oil contamination level.")
        elif "motor" in equipment_text:
            recommendations.append("Perform vibration spectrum review, rotor balance check, and motor bearing inspection.")
        elif equipment_id == "HRM-COIL-03":
            recommendations.append(
                "Inspect wrapper roll alignment, mandrel segment wear, and expansion-drive looseness."
            )
        elif equipment_id == "HRM-FURN-02":
            recommendations.append(
                "Inspect walking beam guides, actuator mounts, and hydraulic pump vibration."
            )
        else:
            recommendations.append(
                "Inspect bearing condition, coupling looseness, and lubrication flow before next campaign."
            )
    if "oil_pressure_bar" in breach_metrics:
        recommendations.append("Verify oil pump delivery, inspect lubrication circuit restriction, and clean asset-specific filters.")
    if "hydraulic_pressure_bar" in breach_metrics:
        recommendations.append("Confirm hydraulic pressure locally, inspect pump cavitation, valve leakage, and seal failure paths.")
    if "roll_gap_variation_mm" in breach_metrics:
        recommendations.append("Check roll alignment, chock clamp torque, and recent roll-change setup.")
    if "motor_current_a" in breach_metrics:
        recommendations.append("Trend motor current against load; inspect mechanical drag and expansion timing.")

    if not history_matches.empty:
        top = history_matches.iloc[0]
        recommendations.append(f"Use prior case {top.record_id} as reference: {top.action_taken}.")

    related_spares = spares[spares.equipment_id == equipment_id].copy()
    blocked = related_spares[(related_spares.available_qty <= 0) | (related_spares.lead_time_days >= 14)].copy()
    blocked = prepare_spares_frame(blocked)
    blocked = blocked.sort_values(["_criticality_score", "lead_time_days"], ascending=[False, False])
    for _, row in blocked.iterrows():
        recommendations.append(
            f"Procurement action: {row.part} has qty={int(row.available_qty)} "
            f"and lead_time={int(row.lead_time_days)} days; escalate now."
        )

    recommendations.append(
        f"Create digital log entry for {sensor_row.equipment_id} with alert {sensor_row.anomaly_alert}."
    )
    return recommendations


def asset_probable_fault(sensor_row: pd.Series, breaches: Sequence[Breach], failure_modes: Sequence[dict]) -> str:
    alert = str(sensor_row.anomaly_alert)
    metric_names = {breach.metric for breach in breaches}
    modes = list(failure_modes)
    if modes:
        if "hydraulic_pressure_bar" in metric_names:
            hydraulic = [mode for mode in modes if any(word in mode["failure_mode"].lower() for word in ["pressure", "seal", "pump", "leak"])]
            if hydraulic:
                return hydraulic[0]["failure_mode"]
        if "oil_pressure_bar" in metric_names:
            oil = [mode for mode in modes if any(word in mode["failure_mode"].lower() for word in ["oil", "gear", "bearing"])]
            if oil:
                return oil[0]["failure_mode"]
        if "temperature_c" in metric_names or "motor_current_a" in metric_names:
            thermal = [mode for mode in modes if any(word in mode["failure_mode"].lower() for word in ["winding", "overheat", "temperature", "motor"])]
            if thermal:
                return thermal[0]["failure_mode"]
        if "vibration_mm_s" in metric_names:
            vibration = [mode for mode in modes if any(word in mode["failure_mode"].lower() for word in ["bearing", "imbalance", "vibration", "gear"])]
            if vibration:
                return vibration[0]["failure_mode"]
        return modes[0]["failure_mode"]
    return alert


def create_report(query: str, equipment_id: Optional[str], data_dir: Path) -> dict:
    sources = load_sources(data_dir)
    return create_report_from_sources(query, equipment_id, sources)


def create_report_from_sources(query: str, equipment_id: Optional[str], sources: dict) -> dict:
    selected_id = select_equipment(query, equipment_id, sources)
    sensors = sources["sensors"]
    sensor_row = sensors[sensors.equipment_id == selected_id].iloc[0]
    spares = sources["spares"]
    history_matches = matched_history(selected_id, query, sources["history"])
    context = retrieve_context(query, selected_id, sources)
    breaches = condition_breaches(sensor_row)
    profile = equipment_profile(selected_id, sources)
    failure_modes = asset_failure_modes(selected_id, sources)
    rul = estimate_rul_with_profile(selected_id, sensor_row, breaches, profile)
    risk = assess_risk(selected_id, breaches, history_matches, spares)
    recommendations = build_recommendations(
        selected_id, sensor_row, breaches, history_matches, spares, risk, failure_modes
    )

    probable_fault = asset_probable_fault(sensor_row, breaches, failure_modes)
    probable_causes = []
    matching_modes = [
        mode for mode in failure_modes
        if str(mode.get("failure_mode", "")).lower() == probable_fault.lower()
    ]
    if matching_modes:
        probable_causes.append(str(matching_modes[0].get("likely_root_cause")))
    if not history_matches.empty:
        probable_causes.extend(str(value) for value in history_matches.root_cause)
    elif failure_modes:
        probable_causes.extend(str(value.get("likely_root_cause")) for value in failure_modes)
    elif breaches:
        probable_causes.append(f"Condition breach detected in {breaches[0].metric}.")
    else:
        probable_causes.append("No strong fault pattern found in current inputs.")
    probable_causes = list(dict.fromkeys(item for item in probable_causes if item))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "agent_steps": [
            "intake maintenance query and optional equipment id",
            "retrieve relevant manuals, SOPs, and historical cases",
            "evaluate condition-monitoring limits",
            "estimate RUL from service age and condition penalty",
            "score risk using condition, history severity, and spares constraints",
            "generate prioritized maintenance and procurement actions",
        ],
        "equipment": {
            "equipment_id": selected_id,
            "equipment_name": sensor_row.equipment_name,
            "active_alert": sensor_row.anomaly_alert,
            "timestamp": sensor_row.timestamp,
            "area": profile.get("area", ""),
            "type": profile.get("type", ""),
            "criticality": profile.get("criticality", ""),
            "status": profile.get("status", ""),
        },
        "diagnosis": {
            "probable_fault": probable_fault,
            "probable_root_causes": probable_causes,
            "condition_breaches": [breach.__dict__ for breach in breaches],
            "asset_failure_modes": failure_modes,
        },
        "prediction": rul,
        "risk": risk,
        "priority": {
            "urgency": "immediate" if risk["level"] in {"critical", "high"} else "planned",
            "plant_bottleneck_priority": rank_bottlenecks(sources, selected_id),
        },
        "recommendations": recommendations,
        "traceability": [
            {
                "source": item.source,
                "title": item.title,
                "score": item.score,
                "detail": compact(item.detail),
            }
            for item in context
        ],
        "assumptions": [
            "RUL is an engineering estimate for demonstration, not a certified prediction.",
            "Thresholds are configurable plant rules and should be calibrated with historian data.",
            "LLM or SLM integration can replace the deterministic reasoning backend while preserving traceability.",
        ],
    }


def compact(text: str, limit: int = 420) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    return normalized if len(normalized) <= limit else normalized[: limit - 3] + "..."


def rank_bottlenecks(sources: dict, selected_id: str) -> List[dict]:
    rows = []
    for _, sensor_row in sources["sensors"].iterrows():
        breaches = condition_breaches(sensor_row)
        history = sources["history"][sources["history"].equipment_id == sensor_row.equipment_id]
        risk = assess_risk(sensor_row.equipment_id, breaches, history, sources["spares"])
        rows.append(
            {
                "equipment_id": sensor_row.equipment_id,
                "equipment_name": sensor_row.equipment_name,
                "risk_score": risk["score"],
                "risk_level": risk["level"],
                "selected": sensor_row.equipment_id == selected_id,
            }
        )
    return sorted(rows, key=lambda row: row["risk_score"], reverse=True)


def write_markdown_report(report: dict, out_file: Path) -> None:
    lines = [
        "# Maintenance Wizard - Tata Steel AI Platform Maintenance Report",
        "",
        "AI-Powered Industrial Reliability & Maintenance Intelligence",
        "",
        f"Generated: {report['generated_at']}",
        f"Equipment: {report['equipment']['equipment_id']} - {report['equipment']['equipment_name']}",
        f"Active alert: {report['equipment']['active_alert']}",
        "",
        "## Diagnosis",
        f"- Probable fault: {report['diagnosis']['probable_fault']}",
        f"- Risk: {report['risk']['level']} ({report['risk']['score']})",
        f"- Urgency: {report['priority']['urgency']}",
        "",
        "Root causes:",
    ]
    lines.extend(f"- {cause}" for cause in report["diagnosis"]["probable_root_causes"])
    lines.extend(["", "Condition breaches:"])
    if report["diagnosis"]["condition_breaches"]:
        for breach in report["diagnosis"]["condition_breaches"]:
            lines.append(
                f"- {breach['metric']}: {breach['value']} breached {breach['level']} limit {breach['limit']}"
            )
    else:
        lines.append("- No current threshold breach.")

    prediction = report["prediction"]
    lines.extend(
        [
            "",
            "## Prediction",
            f"- Health index: {prediction['health_index']}",
            f"- Estimated RUL: {prediction.get('rul_label', str(prediction['estimated_remaining_useful_life_hours']) + ' hours')}",
            f"- RUL explanation: {prediction.get('rul_explanation', 'Estimated from service age and condition penalties.')}",
            f"- Method: {prediction['method']}",
            "",
            "## Recommended Actions",
        ]
    )
    lines.extend(f"{idx}. {item}" for idx, item in enumerate(report["recommendations"], start=1))
    lines.extend(["", "## Traceability"])
    lines.extend(
        f"- {item['source']} / {item['title']} (score {item['score']}): {item['detail']}"
        for item in report["traceability"]
    )
    out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_alert_report(data_dir: Path, out_file: Path) -> None:
    sources = load_sources(data_dir)
    rows = rank_bottlenecks(sources, selected_id="")
    rows = [
        {
            "equipment_id": row["equipment_id"],
            "equipment_name": row["equipment_name"],
            "risk_score": row["risk_score"],
            "risk_level": row["risk_level"],
        }
        for row in rows
    ]
    with out_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["equipment_id", "equipment_name", "risk_score", "risk_level"],
        )
        writer.writeheader()
        writer.writerows(rows)


def append_feedback(out_dir: Path, equipment_id: str, feedback: str) -> None:
    log_file = out_dir / "feedback_log.csv"
    exists = log_file.exists()
    with log_file.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "equipment_id", "feedback"])
        if not exists:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "equipment_id": equipment_id,
                "feedback": feedback,
            }
        )


def append_digital_log(out_dir: Path, report: dict) -> None:
    log_file = out_dir / "digital_maintenance_log.csv"
    exists = log_file.exists()
    with log_file.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "timestamp",
                "equipment_id",
                "alert",
                "risk_level",
                "urgency",
                "probable_fault",
                "first_action",
            ],
        )
        if not exists:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": report["generated_at"],
                "equipment_id": report["equipment"]["equipment_id"],
                "alert": report["equipment"]["active_alert"],
                "risk_level": report["risk"]["level"],
                "urgency": report["priority"]["urgency"],
                "probable_fault": report["diagnosis"]["probable_fault"],
                "first_action": report["recommendations"][0] if report["recommendations"] else "",
            }
        )


def run_once(args: argparse.Namespace) -> dict:
    report = create_report(args.query, args.equipment_id, args.data_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "maintenance_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    write_markdown_report(report, args.out_dir / "maintenance_report.md")
    write_alert_report(args.data_dir, args.out_dir / "alert_report.csv")
    append_digital_log(args.out_dir, report)
    if args.feedback:
        append_feedback(args.out_dir, report["equipment"]["equipment_id"], args.feedback)
    return report


def run_demo(data_dir: Path, out_dir: Path) -> List[dict]:
    demo_queries = json.loads((data_dir / "demo_queries.json").read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    reports = []
    for item in demo_queries:
        report = create_report(item["query"], item.get("equipment_id"), data_dir)
        reports.append(report)
        stem = item["name"]
        (out_dir / f"{stem}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        write_markdown_report(report, out_dir / f"{stem}.md")
        append_digital_log(out_dir, report)
    write_alert_report(data_dir, out_dir / "alert_report.csv")
    return reports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Maintenance Wizard - Tata Steel AI Platform")
    parser.add_argument("--data-dir", default=Path("data"), type=Path)
    parser.add_argument("--out-dir", default=Path("outputs"), type=Path)
    parser.add_argument(
        "--query",
        default=(
            "Finishing mill has high drive-side vibration and chatter marks. "
            "Diagnose the issue and prioritize maintenance actions."
        ),
    )
    parser.add_argument("--equipment-id", default=None)
    parser.add_argument("--feedback", default=None)
    parser.add_argument("--demo", action="store_true", help="Run all bundled sample scenarios")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.demo:
        reports = run_demo(args.data_dir, args.out_dir)
        summary = [
            {
                "equipment_id": report["equipment"]["equipment_id"],
                "risk": report["risk"],
                "first_action": report["recommendations"][0],
            }
            for report in reports
        ]
        print(json.dumps(summary, indent=2))
        return

    report = run_once(args)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
