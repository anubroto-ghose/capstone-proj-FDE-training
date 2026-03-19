# Start Here

Use this file if you want the fastest path to run the project.

## 1) Open Project Root
Windows (PowerShell):
```powershell
cd .
```
POSIX (bash/zsh/sh):
```bash
cd .
```

## 2) Ensure Environment Variables
At minimum:
- `OPENAI_API_KEY`
- `DB_CONNECTION_STRING`

Example DB string:
```text
host=localhost port=5432 dbname=IncidentResolutionDB user=postgres password=root connect_timeout=10 sslmode=prefer
```

## 3) Run One-Time Setup / Re-ingestion
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

Expected artifacts:
- Milvus collection: `incident_response_vectors`
- BM25 file: `source/vector_db/bm25_index_incident_response_v2.pkl`

## 4) Start Backend Services (3 terminals)

Terminal A:
Windows (PowerShell):
```powershell
cd source\auth
uvicorn app.main:app --port 8001
```
POSIX (Linux/macOS/Unix):
```bash
cd source/auth
uvicorn app.main:app --port 8001
```

Terminal B:
Windows (PowerShell):
```powershell
cd source\dashboard-api
uvicorn app.main:app --port 8002
```
POSIX (Linux/macOS/Unix):
```bash
cd source/dashboard-api
uvicorn app.main:app --port 8002
```

Terminal C:
Windows (PowerShell):
```powershell
cd source\agents-api
uvicorn app.main:app --port 8003
```
POSIX (Linux/macOS/Unix):
```bash
cd source/agents-api
uvicorn app.main:app --port 8003
```

## 5) Start Frontend
Windows (PowerShell):
```powershell
cd source\frontend
npm install
npm run dev
```
POSIX (Linux/macOS/Unix):
```bash
cd source/frontend
npm install
npm run dev
```

## 6) Quick Health Check
- Login/Register on frontend
- Create a new session
- Ask:
  - `The load balancer is overwhelmed and requests are timing out. What should we check first?`

You should get:
- similar incident retrieval
- proposed resolution
- validation summary
- estimated resolution time and fix-accuracy signal

## 7) Common Issues
- `ValueError ... split '='`: check `DB_CONNECTION_STRING` formatting (`dbname=` with single `=`).
- No retrieval results: re-run setup scripts and verify Milvus is running.
- Agent not escalating: ask explicitly `Please hand this over to L2`.

## 8) Optional Tests
Windows (PowerShell):
```powershell
cd source\agents-api
pytest tests -q
```
POSIX (Linux/macOS/Unix):
```bash
cd source/agents-api
pytest tests -q
```

DeepEval:
- create/update `source/agents-api/.env.tests`
- set:
  - `RUN_DEEPEVAL=1`
  - `OPENAI_API_KEY=<your_key>`

Then:
Windows (PowerShell):
```powershell
pytest tests/test_eval.py -q
```
POSIX (Linux/macOS/Unix):
```bash
pytest tests/test_eval.py -q
```
