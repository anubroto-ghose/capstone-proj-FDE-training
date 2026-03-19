# AI-Powered Incident Knowledge Base Assistant

Semantic retrieval + multi-agent troubleshooting platform for IT incidents.

## What This Project Does
- Retrieves similar incidents from historical data using hybrid search (BM25 + Milvus).
- Uses a multi-tier agent workflow (L1 -> L2 -> RCA) for escalation.
- Validates suggested fixes with LLM-as-judge.
- Persists sessions, messages, feedback, and A2A handoff context in PostgreSQL.

## Repository Layout
All runnable code is under `source/`.

- `source/auth` -> Auth microservice
- `source/dashboard-api` -> Session/history/dashboard microservice
- `source/agents-api` -> Retrieval + agent orchestration microservice
- `source/frontend` -> Vite + React frontend
- `source/setup` -> One-time setup/ingestion scripts
- `source/data` -> Dataset files
- `source/vector_db` -> BM25 index artifact(s)
- `docs` -> architecture/design/presentation docs

## Dataset (Current)
- File: `source/data/incident_response_dataset_150_rows.xlsx - Incident Data.csv`
- Schema:
  - `Media Asset`
  - `Category`
  - `Ticket ID`
  - `Incident ID`
  - `Incident Details`
  - `Description`
  - `Solution`

## Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL
- Milvus standalone (running on localhost:19530)
- OpenAI API key

## Environment Variables
Set per service `.env` files (or global env), especially:

- `OPENAI_API_KEY=<your_key>`
- `DB_CONNECTION_STRING=host=localhost port=5432 dbname=IncidentResolutionDB user=postgres password=root connect_timeout=10 sslmode=prefer`

## Setup Order (Run Once / Re-run on Data Refresh)
From project root:

Windows (PowerShell):
```powershell
cd source\setup
python postgres_check.py
python postgres_sql_setup.py
python build_bm25_index.py
python csv_to_vector_db.py
```

POSIX (Linux/macOS/Unix):
```bash
cd source/setup
python postgres_check.py
python postgres_sql_setup.py
python build_bm25_index.py
python csv_to_vector_db.py
```

This creates/updates:
- PostgreSQL tables + incident data
- BM25 artifact: `source/vector_db/bm25_index_incident_response_v2.pkl`
- Milvus collection: `incident_response_vectors`

## Run Services
Open separate terminals from project root.

Auth API:
Windows (PowerShell):
```powershell
cd source\auth
uvicorn app.main:app --port 8001
```
POSIX:
```bash
cd source/auth
uvicorn app.main:app --port 8001
```

Dashboard API:
Windows (PowerShell):
```powershell
cd source\dashboard-api
uvicorn app.main:app --port 8002
```
POSIX:
```bash
cd source/dashboard-api
uvicorn app.main:app --port 8002
```

Agents API:
Windows (PowerShell):
```powershell
cd source\agents-api
uvicorn app.main:app --port 8003
```
POSIX:
```bash
cd source/agents-api
uvicorn app.main:app --port 8003
```

Frontend:
Windows (PowerShell):
```powershell
cd source\frontend
npm install
npm run dev
```
POSIX:
```bash
cd source/frontend
npm install
npm run dev
```

## Testing
Auth:
Windows (PowerShell):
```powershell
cd source\auth
pytest tests -q
```
POSIX:
```bash
cd source/auth
pytest tests -q
```

Dashboard:
Windows (PowerShell):
```powershell
cd source\dashboard-api
pytest tests -q
```
POSIX:
```bash
cd source/dashboard-api
pytest tests -q
```

Agents:
Windows (PowerShell):
```powershell
cd source\agents-api
pytest tests -q
```
POSIX:
```bash
cd source/agents-api
pytest tests -q
```

DeepEval (optional online eval):
- Use `source/agents-api/.env.tests`
- Include:
  - `RUN_DEEPEVAL=1`
  - `OPENAI_API_KEY=<your_key>`

Then:
Windows (PowerShell):
```powershell
cd source\agents-api
pytest tests/test_eval.py -q
```
POSIX:
```bash
cd source/agents-api
pytest tests/test_eval.py -q
```

## Docs
Start with:
- `docs/diagram_index.md`
- `docs/design_decisions.md`
- `docs/ppt_creation_prompt.md`

## Quick Start
If you want command-only onboarding, read:
- `Start_Here.md`
