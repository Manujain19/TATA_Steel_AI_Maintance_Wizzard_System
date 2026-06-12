# Maintenance Wizard - AI Engineer Stack Modernization

## Architecture Diagram

```mermaid
flowchart LR
  UI["Existing Web UI"] --> API["FastAPI Backend"]
  API --> DB["PostgreSQL"]
  API --> RAG["Hybrid RAG Pipeline"]
  API --> AGENTS["LangGraph Multi-Agent Workflow"]
  API --> WS["WebSockets"]
  RAG --> BM25["BM25 Keyword Search"]
  RAG --> EMB["Embedding Service: BGE / MiniLM / Nomic"]
  RAG --> RERANK["Cross-Encoder Reranker"]
  EMB --> VS["VectorStore Interface"]
  VS --> CHROMA["ChromaDB Dev Store"]
  VS --> QDRANT["Qdrant Production Store"]
  AGENTS --> TOOLS["Tool Calling Agents"]
  AGENTS --> LLM["LLM Router: Groq/OpenAI/Anthropic/Gemini/Ollama"]
  AGENTS --> OBS["LangSmith + Local Observability"]
  API --> FILES["JSON Seed Data"]
```

## Updated Folder Structure

```text
backend/
  api/
  agents/
    tool_agents.py
  rag/
    hybrid_retriever.py
  vectorstores/
  services/
  models/
  db/
  embeddings/
  memory/
  reports/
  telemetry/
  tests/
frontend/
  components/
  pages/
  hooks/
  services/
data/
  manuals/
  sops/
  failures/
  maintenance/
```

## Database Schema

```sql
assets(id, payload)
sensor_data(id, equipment_id, payload)
sensor_history(id, equipment_id, payload)
failure_modes(id, equipment_id, payload)
failure_reports(record_id, equipment_id, payload)
maintenance_logs(log_id, equipment_id, payload)
spare_parts(part_id, equipment_id, payload)
work_orders(work_order_id, equipment_id, payload)
copilot_conversations(id, equipment_id, payload, created_at)
sector_health(sector, payload)
asset_relationships(id, source_asset, target_asset, payload)
```

## LangGraph Workflow Diagram

```mermaid
flowchart TD
  Q["User Query"] --> R["Retriever Agent"]
  R --> D["Diagnosis Agent"]
  D --> RCA["Root Cause Agent"]
  RCA --> MP["Maintenance Planner Agent"]
  MP --> INV["Inventory Agent"]
  INV --> EX["Executive Agent"]
  EX --> OUT["Final Response"]
  RCA --> RCA_TOOLS["retrieve_failures / compare_failure_patterns / generate_rca"]
  MP --> WO_TOOLS["generate_work_order / assign_priority / estimate_duration"]
  INV --> INV_TOOLS["check_stock / recommend_spares / calculate_lead_time"]
  EX --> EX_TOOLS["business_impact / risk_exposure / executive_summary"]
```

## RAG Pipeline Diagram

```mermaid
flowchart TD
  DOCS["Manuals, SOPs, Logs, Reports, Work Orders, Spares"] --> LOAD["Document Loader"]
  LOAD --> CHUNK["Chunking Pipeline"]
  CHUNK --> BM25["BM25 Index"]
  CHUNK --> EMB["Embedding Pipeline"]
  EMB --> STORE["ChromaDB or Qdrant"]
  QUERY["User Query"] --> BQ["BM25 Search"]
  QUERY --> QEMB["Query Embedding"]
  QEMB --> VS["Vector Search"]
  BM25 --> BQ
  STORE --> VS
  BQ --> MERGE["Merge + Hybrid Score"]
  VS --> MERGE
  MERGE --> RERANK["Cross-Encoder Rerank"]
  RERANK --> CTX["Top Context + Citations"]
  CTX --> LLM["LLM"]
  LLM --> RESP["Grounded Response"]
```

## Migration Summary

- Added FastAPI backend with REST, Swagger/OpenAPI, static frontend serving, and WebSocket endpoints.
- Added Pydantic request models.
- Added PostgreSQL schema and JSON seed loader.
- Added Hybrid RAG document loader, chunker, BM25 keyword search, embedding service, vector retrieval, merge scoring, reranking, and context assembly.
- Added VectorStore abstraction with ChromaDB and Qdrant adapters plus in-memory fallback.
- Added LangGraph-compatible multi-agent workflow with tool calling agents for work orders, inventory, root cause analysis, and executive decision support.
- Added LLM router preserving Llama/Groq fallback and deployment-ready provider expansion.
- Added conversation memory, streaming LLM facade, source citations, confidence engine, LangSmith-ready observability, Dockerfile, Docker Compose, and pytest coverage.

## Validation Report

Run:

```powershell
python -m py_compile backend/main.py backend/agents/langgraph_workflow.py backend/rag/pipeline.py
pytest backend/tests
uvicorn backend.main:app --port 8012
```

Expected:

- Existing UI still loads at `/`.
- Swagger available at `/docs`.
- Current frontend API behavior preserved.
- New routes available: `/api/assets`, `/api/sensors`, `/api/failures`, `/api/workorders`, `/api/copilot`, `/api/reports`, `/api/rul`, `/api/business-impact`, `/api/digital-twin`, `/api/search`.
