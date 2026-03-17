# AI-Powered Incident Knowledge Base Assistant

A semantic retrieval and multi-agent system designed to streamline IT support by leveraging historical incident data. This system uses a multi-tier agent architecture (L1, L2, RCA) to triage, investigate, and resolve technical issues with high accuracy and speed.

## 🚀 Key Features

### 🔹 Requirement 1 (Basic)
- **Hybrid RAG**: Combined semantic search (Milvus) and keyword search (BM25) for precise incident retrieval.
- **Triage Agent**: Automated priority (P1-P4) and category classification.
- **Metadata Filtering**: Advanced filtering by priority, impact, and category.
- **Guardrails**: Input/Output PII masking using Microsoft Presidio.
- **Microservices Architecture**: Separate Auth, Dashboard, and Agents APIs.

### 🔹 Requirement 2 (Advanced)
- **Multi-Tier Agent System**: Seamless handoff between L1 Generalist, L2 Technical Specialist, and RCA Specialist.
- **Predictive Metrics**: Automated resolution time prediction and fix accuracy scoring.
- **Agent Collaboration (A2A)**: Structured knowledge sharing between agents via dedicated context tools.
- **Continuous Improvement**: Feedback loop for users to rate resolutions (thumbs up/down).
- **Token Optimization**: History compression for long-running troubleshooting sessions.
- **DeepEval Integration**: Quality assurance for RAG responses using relevancy and faithfulness metrics.

## 🛠️ Project Setup

### 1. Prerequisites
- Python 3.9+
- PostgreSQL
- Milvus (Standalone)
- Node.js & npm (for Frontend)

### 2. Backend Setup
Each microservice has its own `.env` file. Ensure they are configured correctly.

```bash
# Start Auth API (Port 8001)
cd auth
uvicorn app.main:app --port 8001

# Start Dashboard API (Port 8002)
cd dashboard-api
uvicorn app.main:app --port 8002

# Start Agents API (Port 8003)
cd agents-api
uvicorn app.main:app --port 8003
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 📊 Sample Usage

1. **Login**: Register/Login via the frontend.
2. **Query**: Enter a natural language query like: *"Our application runs fine after a restart but after some time it starts slowing down. What might be causing this?"*
3. **Response**: 
   - An L1 agent will triage the issue.
   - If complex, it hands off to L2 or the RCA Specialist.
   - The system retrieves similar incidents from Milvus/BM25.
   - A resolution is presented with **Predicted Resolution Time** and **Fix Accuracy Score**.
4. **Feedback**: Rate the response to improve the knowledge base.

## 🏗️ Architecture

The system follows a modular microservice architecture. See `architecture_and_design.md` for a detailed Mermaid diagram and technical decisions.

## 🧪 Evaluation
Run DeepEval tests to verify RAG quality:
```bash
cd agents-api
pytest tests/test_eval.py
```

## ✅ Test Suite (Read-Only)
The automated tests below focus on **data retrieval / matching behavior** and avoid insert/delete test cases.

### Auth Microservice
```bash
cd auth
pip install -r requirements.txt pytest
pytest tests/test_auth_read_only.py -q
```

### Dashboard API
```bash
cd dashboard-api
pip install -r requirements.txt pytest pytest-asyncio
pytest tests/test_dashboard_read_only.py -q
```

### Agents API (Retrieval + DeepEval)
```bash
cd agents-api
pip install -r requirements.txt pytest pytest-asyncio deepeval
pytest tests/test_retrieval_service_read_only.py -q
# DeepEval (online, opt-in via agents-api/.env.tests)
# Example .env.tests:
# RUN_DEEPEVAL=1
# OPENAI_API_KEY=your_key
pytest tests/test_eval.py -q
```

### Run all service tests
```bash
cd auth && pytest tests -q
cd ../dashboard-api && pytest tests -q
cd ../agents-api && pytest tests -q
```

Note:
- `tests/test_eval.py` uses DeepEval LLM metrics and runs only when:
  - `RUN_DEEPEVAL=1` (for example via `agents-api/.env.tests`)
  - `OPENAI_API_KEY` is set (for example via `agents-api/.env.tests`)
