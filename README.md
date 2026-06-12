# Maintenance Wizard - Tata Steel AI Platform

**Author / Creator:** Manu Jain  
**Role:** AI Engineer

This repository contains an enterprise-style industrial maintenance copilot for
hot rolling assets. The goal is to support maintenance engineers, production
supervisors, reliability teams, procurement owners, and plant leadership with
diagnosis, root-cause reasoning, abnormality detection, RUL estimation,
business-impact analysis, maintenance planning, spares decisions, reports, and
auditability.

The original `src/train_predict.py` defect-classification experiment is still
kept in the repo as a legacy model. The production maintenance assistant is
implemented through `src/maintenance_wizard.py`, `src/web_app.py`, and the
agent services in `services/`.

## What It Does

- Accepts natural-language maintenance queries.
- Integrates equipment manuals, SOPs, historical failures, sensor summaries,
  and spare inventory.
- Detects abnormal sensor conditions with warn/trip limits.
- Estimates remaining useful life using service age plus condition penalties.
- Scores risk using condition severity, historical severity, and procurement
  constraints.
- Produces structured JSON, engineer-readable Markdown, alert CSV, and digital
  maintenance log outputs.
- Captures engineer feedback for continuous improvement.

## Run the Demo

```powershell
& "C:\Users\mjain\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\src\maintenance_wizard.py --demo
```

Demo outputs are written to `outputs/`:

- `outputs/finishing_mill_vibration.json`
- `outputs/finishing_mill_vibration.md`
- `outputs/down_coiler_expansion_failure.json`
- `outputs/down_coiler_expansion_failure.md`
- `outputs/furnace_walking_beam_delay.json`
- `outputs/furnace_walking_beam_delay.md`
- `outputs/alert_report.csv`
- `outputs/digital_maintenance_log.csv`

## Run the Frontend

Start the production FastAPI app from the VS Code terminal:

```powershell
cd "C:\Users\mjain\Documents\Defect Detection in Hot Rolling"
uvicorn backend.main:app --host 127.0.0.1 --port 8012
```

Open:

```text
http://127.0.0.1:8012
```

The AI embedding and reranking models are not loaded during FastAPI startup or
normal requests by default, so Uvicorn starts quickly. To intentionally preload
models during startup, set this in `.env`:

```text
EAGER_LOAD_AI_MODELS=true
```

For production-style RAG performance, build the vector store once outside the
API request path:

```powershell
python .\scripts\build_vector_store.py --vector-db chromadb
```

Runtime requests do not rebuild the vector index unless this flag is explicitly
enabled:

```text
AUTO_INDEX_VECTOR_STORE=true
```

The legacy standard-library web app is still available:

```powershell
cd "C:\Users\mjain\Documents\Defect Detection in Hot Rolling"
& "C:\Users\mjain\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\src\web_app.py
```

Open:

```text
http://127.0.0.1:8000
```

If port `8000` is already busy, run:

```powershell
& "C:\Users\mjain\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\src\web_app.py --port 8010
```

Then open:

```text
http://127.0.0.1:8010
```

The frontend includes the equipment dashboard, natural-language analysis form,
plant alert prioritization, RUL/risk summary, traceability view, spare status,
demo scenario runner, and feedback capture.

Production platform features:

- Industrial Maintenance Copilot directly below asset selection with suggested
  actions for vibration analysis, similar failures, RUL prediction, work-order
  generation, spare risk review, and shutdown planning.
- Executive Decision Summary for top plant risk, expected production impact,
  recommended maintenance strategy, avoided downtime, avoided cost, and
  required approvals.
- Executive KPIs, Digital Twin Health, and Business Impact Analysis as the core
  dashboard views.
- Investigation Timeline using business-friendly completion steps rather than
  internal software component names.
- Evidence Used view separating manual references, SOP references, historical
  failures, sensor evidence, and reasoning summary.
- Enterprise Work Order with lifecycle status, assigned team, required skills,
  required spares, safety permits, estimated downtime, estimated repair cost,
  PDF download, JSON export, and saved audit record.
- Plant Incident Replay for reviewing historical failure progression,
  production impact, corrective actions, and lessons learned.
- Knowledge Center for equipment manuals, SOP repository, historical failure
  records, sensor event repository, work-order history, and spare inventory
  knowledge.
- Runtime event ingestion, knowledge search, plant alerts, spare risk register,
  and maintenance feedback capture.

## Advanced API Endpoints

The local web server exposes these endpoints for the frontend:

- `GET /api/bootstrap`: equipment, spares, history, alerts, role notifications,
  and live monitor seed data.
- `GET /api/live`: refreshed simulated condition-monitoring trends.
- `GET /api/intelligence`: executive KPIs, maintenance plan, and digital twins.
- `GET /api/enterprise`: enterprise maintenance dashboards including handover,
  criticality, budget, RCA, timeline, procurement, workload, audit, and field
  mode.
- `POST /api/analyze`: natural-language diagnosis and recommendation report.
  This also runs the multi-agent orchestrator and writes
  `outputs/agentic_report.json`.
- `POST /api/what-if`: temporary sensor override scenario analysis.
- `POST /api/work-order`: generates a structured enterprise maintenance work
  order.
- `POST /api/save-work-order`: saves the work order status and audit event.
- `GET /api/work-order-pdf`: downloads the latest work order as a PDF.
- `GET /api/shift-handover-pdf`: downloads the shift handover as a PDF.
- `POST /api/knowledge-search`: retrieves relevant manuals, SOPs, and cases.
- `GET /api/knowledge-center`: returns indexed manuals, SOPs, history, sensor
  events, work-order history, and spare inventory knowledge metadata.
- `POST /api/ingest`: captures runtime logs, reports, alerts, process notes, or
  spare updates.
- `POST /api/chat`: supports multi-turn engineer troubleshooting.
- `POST /api/operation-simulator`: calculates strategy risk, cost, and
  production impact.
- `POST /api/plant-incident-demo`: runs the 5-second autonomous plant incident
  demo for the Down Coiler Mandrel and returns report, agents, work order,
  enterprise dashboards, and alerts.
- `POST /api/demo`: generates all bundled demo reports.
- `POST /api/feedback`: stores engineer feedback in `outputs/feedback_log.csv`.

## Optional Intelligence Engine Keys

The system runs without API keys using local reasoning. To enable an external
decision engine, configure provider keys in `.env` before starting the server.
Use `.env.example` as a safe template for Groq, vector-store, embedding,
reranker, PostgreSQL, and LangSmith settings.

Diagnostics:

```powershell
Invoke-RestMethod http://127.0.0.1:8012/api/system-health
Invoke-RestMethod http://127.0.0.1:8012/api/performance
Invoke-RestMethod http://127.0.0.1:8012/api/performance-health
Invoke-RestMethod "http://127.0.0.1:8012/api/llm-health?run_test=true"
```

If no key is present, Maintenance Wizard still produces structured JSON, investigation
timelines, confidence, and executive summaries.

## Ask a Custom Query

```powershell
& "C:\Users\mjain\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\src\maintenance_wizard.py --equipment-id HRM-COIL-03 --query "Down coiler mandrel expansion failed twice and tail-end slip is visible. What should maintenance do first?"
```

Add engineer feedback after a run:

```powershell
& "C:\Users\mjain\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\src\maintenance_wizard.py --equipment-id HRM-ROLL-01 --feedback "Confirmed low lubrication flow; bearing replacement planned."
```

## Project Structure

- `src/maintenance_wizard.py`: agentic maintenance decision pipeline.
- `src/web_app.py`: local web server and JSON API for the frontend.
- `services/llm_provider.py`: secure external decision-engine adapter with local reasoning fallback.
- `services/agent_orchestrator.py`: Sensor, Diagnosis, Knowledge, Root Cause,
  Risk, Spare, Planner, and Work Order agents.
- `web/`: frontend HTML, CSS, and JavaScript.
- `data/equipment_manuals.md`: equipment knowledge base.
- `data/maintenance_sops.md`: maintenance SOP extracts.
- `data/failure_history.csv`: historical failure records.
- `data/sensor_snapshot.csv`: current condition-monitoring snapshot.
- `data/spares_inventory.csv`: spare part availability and lead time.
- `docs/architecture.md`: architecture, flow, assumptions, and limitations.

## Deployment Notes

The system can run offline with deterministic local reasoning, or it can use
configured LLM providers when API keys are configured. The report `traceability` section
shows the manual, SOP, and historical evidence behind each recommendation while
preserving the same data flow, risk scoring, alerting, and feedback loop.

For cloud deployment, use the included Dockerfile and Render blueprint:

- `Dockerfile`
- `render.yaml`
- `DEPLOYMENT.md`

Recommended public demo deployment:

```bash
git push origin main
```

Then create a Render Blueprint from the GitHub repository and set:

```text
GROQ_API_KEY=your_groq_key_here
```

Render will run the app on its assigned `$PORT` and serve the frontend plus APIs
from the same public URL.

## Legacy Defect Model

The previous coil defect model can still be run with:

```powershell
$env:PYTHONPATH="$PWD\.deps"
& "C:\Users\mjain\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\src\train_predict.py --data-dir "C:\Users\mjain\Downloads\169df72b552611f1\dataset"
```
