# AI-Powered Incident Knowledge Base Assistant

This microservice provides an AI-driven support interface for IT teams to query historical incidents and retrieve resolutions.

## Project Structure
- `app/agents/`: L1, L2, and L3 (RCA) support agents with handoff logic.
- `app/services/`: Hybrid retrieval service (Milvus + BM25) and session management.
- `app/tools/`: Custom tools for agents (Search, Handoffs).
- `app/utils/`: Guardrails (PII masking), Telemetry (LangSmith), and Logging.
- `app/routes/`: FastAPI chat endpoints.

## Setup Instructions
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure `.env`:
   - `OPENAI_API_KEY`: Your OpenAI key.
   - `DB_CONNECTION_STRING`: PostgreSQL connection string.
   - `MILVUS_URL`: Milvus server URL.
   - `AUTH_BASE_URL`: Standalone auth service URL.
3. Start the service:
   ```bash
   uvicorn app.main:app --port 8002
   ```

## Sample Usage
**Endpoint**: `POST /chat/message`
**Payload**:
```json
{
  "session_id": "test_session_001",
  "message": "The application is slowing down after a restart. What should I check?"
}
```
**Expected Behavior**:
- L1 Agent triage.
- Hybrid search retrieves similar "memory leak" or "resource exhaustion" incidents.
- Agent suggests resolutions based on past closure codes.
- Usage and structure are persisted in PostgreSQL.
