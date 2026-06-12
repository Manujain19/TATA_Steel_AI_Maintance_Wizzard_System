# Maintenance Wizard - Tata Steel AI Platform Architecture

## Purpose

Maintenance Wizard is an offline-capable decision-support system for steel plant
maintenance engineers, reliability teams, production supervisors, and
procurement owners. It accepts natural-language troubleshooting questions and
combines plant knowledge, historical failures, sensor summaries, work orders,
and spare constraints to produce structured, traceable maintenance decisions.

## Components

- `src/maintenance_wizard.py`: command-line agent pipeline.
- `src/web_app.py`: local web server, JSON APIs, role routing, live monitor,
  and what-if scenario orchestration.
- `web/`: browser frontend for the maintenance command center.
- `data/equipment_manuals.md`: equipment-specific operating knowledge.
- `data/maintenance_sops.md`: troubleshooting and escalation rules.
- `data/failure_history.csv`: historical cases used for diagnosis and root
  cause matching.
- `data/sensor_snapshot.csv`: current condition-monitoring snapshot.
- `data/spares_inventory.csv`: spare availability and procurement lead times.
- `outputs/maintenance_report.json`: structured machine-readable output.
- `outputs/maintenance_report.md`: engineer-readable report.
- `outputs/alert_report.csv`: plant-level risk prioritization.
- `outputs/digital_maintenance_log.csv`: automatic maintenance log entries.

## Agent Flow

1. Intake the user query and optional equipment ID.
2. Select the most relevant equipment from the query and current alerts.
3. Retrieve supporting context from manuals, SOPs, and historical cases.
4. Evaluate condition-monitoring data against plant thresholds.
5. Estimate remaining useful life from service age and condition penalties.
6. Score risk using condition severity, historical severity, and spare delays.
7. Generate prioritized action, procurement, and monitoring recommendations.
8. Write reports, alerts, and a digital maintenance log entry.

## Investigation Workflow

The system includes an internal multi-step orchestrator in
`services/agent_orchestrator.py`. The web `Run Investigation` action presents
the result as a business-facing maintenance timeline:

- Sensor Analysis Completed
- Historical Failure Review Completed
- SOP Validation Completed
- Risk Assessment Completed
- Work Order Generated

The UI intentionally hides internal software component names and renders the
workflow as completed maintenance decision steps with timestamps and evidence.

## Intelligence Engine Provider

`services/llm_provider.py` supports secure external decision-engine providers
and offline reasoning mode. If no provider key is set, the offline engine still
returns strict JSON for diagnosis, risk explanation, recommendations,
executive summary, and confidence estimate.

## Reasoning Trace

The orchestrator returns a transparent reasoning trace:

- Observed evidence from sensor threshold breaches.
- Retrieved context from manuals, SOPs, and historical cases.
- Reasoning statements linking evidence to probable root cause and risk.
- AI confidence score calculated from retrieval relevance, historical matches,
  anomaly severity, and LLM confidence estimate.

## Advanced Prototype Features

- Enterprise maintenance workflow: shift handover with PDF export, asset
  criticality matrix, business impact analysis, budget view, RCA workspace,
  failure prediction timeline, operations impact simulation, KPI dashboard,
  audit trail, procurement recommendations, team workload, and mobile
  technician mode.
- Live monitor: the web server generates deterministic simulated trend points
  for temperature, vibration, motor current, and hydraulic pressure. This
  demonstrates how real historian or IoT feeds would appear in the interface.
- What-if analysis: users can override key sensor values in the frontend. The
  server evaluates the temporary scenario without changing source CSV data.
- Role-based routing: alerts are translated into maintenance, production, and
  procurement notifications so each stakeholder sees action-oriented messages.
- Plant prioritization: all equipment is ranked by bottleneck risk using
  condition, historical severity, and spare constraints.
- Executive intelligence: readiness, downtime exposure, spare blockers, and top
  bottlenecks are summarized for supervisors.
- Digital twin health: each asset receives component health scores for thermal,
  mechanical, electrical, hydraulic, and process condition.
- Maintenance planning: ranked assets are converted into schedule windows with
  estimated duration and spare-blocker status.
- Enterprise work-order generation: recommendations become executable tasks
  with lifecycle status, assigned team, safety steps, approvals, required
  parts, cost, manpower, shutdown duration, PDF download, JSON export, and
  acceptance criteria.
- Knowledge search: manual, SOP, and historical-failure evidence can be searched
  independently of a full analysis run.
- Feedback capture: engineer corrections are stored for later threshold tuning,
  retrieval improvement, or model fine-tuning.

## Reasoning and Traceability

The prototype uses deterministic retrieval and scoring so that every output can
be explained during judging. The `traceability` section in each JSON report
points to the manual/SOP/history snippets used by the agent. A production
version can replace the deterministic summarizer with an LLM or SLM while
keeping the same retrieval, evidence, risk, and report structure.

## Prediction Logic

Abnormality detection is threshold-based for the demo. Each sensor breach is
classified as `warn` or `trip`. The RUL estimate starts from the equipment
service interval and applies a penalty based on active breaches. This should be
calibrated with real historian data before production use.

## Feedback Loop

Engineer feedback can be appended with `--feedback`. The feedback log is stored
in `outputs/feedback_log.csv` and can be used later to tune thresholds, improve
case matching, or fine-tune an LLM/SLM reasoning backend.

## Assumptions

- Sample data is synthetic but realistic for a hot rolling maintenance context.
- Sensor limits are plant rules for demonstration and need site calibration.
- The prototype is offline by design; external APIs are not required to run it.
- Reports support decision-making and should not replace certified plant safety
  procedures.
