# Design Decisions and Approach

## 1. Problem Framing and Approach
The goal is to help IT support teams quickly resolve recurring incidents by retrieving similar historical tickets and surfacing actionable resolution context.

Our approach is:
1. Build a hybrid retrieval core (semantic + keyword) so both intent and exact terms are handled.
2. Add a multi-tier agent workflow (L1 -> L2 -> RCA) to mirror real support escalation.
3. Keep every interaction auditable with persisted sessions, usage, feedback, and trace logs.
4. Expose all capabilities through microservice APIs and a lightweight frontend for operational use.

This balances retrieval quality, explainability, and extensibility for production-like ITSM usage.

## 2. High-Level Architecture Rationale
We use a microservices architecture with clear responsibilities:
- Auth API: identity and token lifecycle.
- Dashboard API: profile/session/history/search/rename retrieval endpoints.
- Agents API: retrieval-augmented troubleshooting and agent orchestration.

Why this split:
- Better separation of concerns and maintainability.
- Independent scaling (Agents API can scale separately due to LLM/retrieval load).
- Cleaner security boundaries (auth concerns isolated from retrieval concerns).

Trade-off:
- Slightly higher operational overhead than a monolith (multiple services/envs).

## 3. Retrieval Design Decisions
### 3.1 Hybrid Search (Milvus + BM25)
Decision:
- Use BM25 keyword matching + vector semantic similarity for incident retrieval.

Why:
- BM25 captures precise terms (error signatures, incident IDs, category words).
- Vector search captures paraphrased intent and natural language symptoms.

Alternative considered:
- Pure vector search only.

Why not chosen:
- Misses strict lexical relevance in many IT ops scenarios (codes/tokens/short signatures).

### 3.2 Metadata Filtering
Decision:
- Support filtering by priority, impact, and category during retrieval.

Why:
- IT support triage depends on operational context, not only text similarity.

Trade-off:
- Requires robust normalization/mapping across user inputs (e.g., P1/P2 forms).

### 3.3 Reranking
Decision:
- Add rerank signals for recency and resolution-success state.

Why:
- Newer and resolved incidents are usually more operationally useful.

Trade-off:
- Slightly more scoring complexity and tuning effort.

## 4. Agent Design Decisions
### 4.1 Multi-tier Agents (L1 -> L2 -> RCA)
Decision:
- Use specialized agent tiers with handoffs instead of one general agent.

Why:
- Better alignment with enterprise support workflows.
- Low complexity issues handled quickly by L1; complex root-cause work escalates.

Alternative considered:
- Single-agent approach.

Why not chosen:
- Less realistic triage behavior and weaker escalation semantics.

### 4.2 A2A Context Sharing
Decision:
- Add Agent-to-Agent context sharing for structured handoff memory.

Why:
- Prevents repeated re-triage across tiers and preserves diagnostic continuity.

Trade-off:
- Adds state management complexity.

## 5. LLM and Tooling Choices
### 5.1 LLM Model
Decision:
- `gpt-4o-mini` for agent execution, LLM-judge, and metrics helper tools.

Why:
- Good quality/latency/cost balance for iterative support interactions.

Alternative considered:
- Larger premium model for all paths.

Why not chosen:
- Higher latency/cost for routine high-volume support flows.

### 5.2 Embeddings
Decision:
- `text-embedding-3-small`.

Why:
- Strong semantic retrieval performance at lower cost.

Alternative:
- Larger embedding model.

Why not chosen:
- Higher cost and larger storage footprint for marginal gains in this use case.

### 5.3 Guardrails
Decision:
- Microsoft Presidio analyzer/anonymizer + domain-specific allow-list tuning.

Why:
- Reliable PII masking layer with extensibility for ITSM-specific false-positive control.

Trade-off:
- Requires iterative tuning of false positives (e.g., relative time phrases).

### 5.4 Prompt Compression
Decision:
- LLMLingua-2 (`microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank`) for long history compression.

Why:
- Reduces token overhead for long-running sessions.

Trade-off:
- Compression can lose nuance if over-aggressive.

## 6. Data Layer Decisions
### 6.1 PostgreSQL as System of Record
Decision:
- Use PostgreSQL for users, sessions, messages, usage, feedback, and incident metadata.

Why:
- Strong relational integrity, mature tooling, and flexible querying for dashboard analytics.

PostgreSQL advantages vs other SQL databases (for this project):
- Rich JSONB support:
  - Useful for semi-structured fields like token usage details without losing SQL query power.
- Strong indexing options:
  - B-tree, GIN, expression indexes support mixed transactional + analytical patterns well.
- Mature ecosystem and observability:
  - Excellent compatibility with SQLAlchemy/FastAPI and strong operational tooling.
- Open-source and cost-efficient:
  - No licensing constraints for capstone/prototype-to-production growth.
- Reliability features:
  - ACID consistency, robust concurrency, and straightforward backup/replication patterns.

Why not alternative SQL choices (in this context):
- MySQL/MariaDB:
  - Good options, but PostgreSQL generally offers stronger advanced query/JSON ergonomics for this workload.
- SQL Server/Oracle:
  - Powerful enterprise options, but heavier operational/licensing footprint for this project scope.

### 6.2 Milvus for Vector Search
Decision:
- Use Milvus for semantic nearest-neighbor retrieval on incident embeddings.

Why:
- Scales better for vector workloads than relational-only approaches.

### 6.3 BM25 Index as Local Artifact
Decision:
- Persist BM25 index as local serialized artifact for fast lexical retrieval.

Why:
- Simple, fast startup/runtime path for deterministic keyword scoring.

## 7. API and Frontend Decisions
### 7.1 API-first Design
Decision:
- Expose all core operations via REST endpoints.

Why:
- Enables both UI use and integration with other tooling.

### 7.2 Frontend Scope
Decision:
- Keep frontend focused: auth, chat, session history, rename/search, feedback.

Why:
- Prioritizes demonstrable end-to-end functionality over heavy UI complexity.

## 8. Evaluation and Quality Decisions
### 8.1 DeepEval for LLM Quality
Decision:
- Add DeepEval relevancy + faithfulness checks with scenario-based cases.

Why:
- Quantifies answer quality and grounding behavior.

### 8.2 Read-only Service Tests
Decision:
- Add read-only tests for retrieval/matching/session listing/history.

Why:
- Validates behavior without destructive data setup/teardown risk.

## 9. Observability and Feedback
### 9.1 Tracing
Decision:
- LangSmith tracing on agent and tool paths (including embedding calls/fallback).

Why:
- Critical for debugging multi-agent/tool call chains and token economics.

### 9.2 Continuous Improvement
Decision:
- Persist thumbs up/down feedback with context (agent tier/category).

Why:
- Provides practical signal for future ranking/prompt improvements.

## 10. Key Trade-offs Summary
- Microservices vs monolith:
  - Chosen microservices for modularity and scale, at cost of operational complexity.
- Hybrid retrieval vs single method:
  - Chosen hybrid for robustness, at cost of more scoring logic.
- Multi-tier agents vs single agent:
  - Chosen tiered workflow for realism and control, at cost of orchestration complexity.
- Cost-efficient models vs highest-capability models:
  - Chosen efficient defaults for practicality under iterative workloads.

## 11. Future Enhancements
1. Add retention policy and indexing strategy for `a2a_context` as volume grows.
2. Add retrieval relevance dashboards and offline benchmark sets.
3. Add role-based access controls and stricter tenant isolation.
4. Introduce async job queue for bulk incident analysis workflows.
5. Expand DeepEval with regression suites tied to real production incident clusters.

## 12. Forward-Looking Architecture Upgrades
### 12.1 Redis + PostgreSQL pattern for A2A context
Current:
- A2A context is now persisted in PostgreSQL.

Future upgrade:
- Add Redis as a low-latency hot store for active-session A2A context.
- Keep PostgreSQL as durable source of truth and recovery store.

Suggested strategy:
1. Write-through:
   - On context post, write to Redis and PostgreSQL.
2. Read path:
   - Read Redis first for active session; fallback to PostgreSQL on cache miss.
3. Recovery:
   - Rehydrate Redis from PostgreSQL if cache is cold or node restarts.

Benefits:
- Lower latency for high-frequency handoff reads.
- Durable audit trail retained in PostgreSQL.
- Better multi-instance horizontal scale.

### 12.2 Separate service endpoints for guardrails and prompt compression
Current:
- Guardrails and compression are embedded in the Agents API runtime flow.

Future upgrade:
- Expose internal endpoints or a sidecar service:
  - `/internal/guardrails/mask`
  - `/internal/compression/compress`

Benefits:
- Reuse by other microservices/tools.
- Independent scaling and versioning.
- Easier A/B testing for guardrail/compression policies.

### 12.3 Vector search scalability roadmap
Current:
- Milvus + BM25 index file provides strong baseline hybrid retrieval.

Future options:
1. Milvus horizontal scaling:
   - Sharding/partitioning by category or time window.
   - Separate online vs historical partitions.
2. Elasticsearch/OpenSearch hybrid stack:
   - Use BM25 + dense vector in one engine for unified ranking pipelines.
   - Useful when organization already operates Elasticsearch.
3. Multi-stage retrieval:
   - Stage 1: fast candidate generation (keyword + ANN)
   - Stage 2: cross-encoder reranker for top-N precision.
   - Optional architecture: isolate Stage 2 as an independent reranking microservice
     when using models like `cross-encoder/ms-marco-MiniLM-L6-v2`.
4. Incremental indexing pipeline:
   - Event-driven ingestion so new incidents are indexed near real time.
5. pgvector option:
   - For smaller deployments, unify vector + relational in PostgreSQL to reduce infra complexity.

Recommended path:
- Keep Milvus for vector scale,
- Add OpenSearch/Elasticsearch only when operationally justified by unified search needs,
- Introduce learned reranking once top-N candidate quality becomes the main bottleneck.

Practical note for this dataset:
- Current `ITSM_data.csv` is predominantly structured metadata
  (CI category, priority, status, timestamps, closure code, etc.) with limited rich narrative text.
- Because cross-encoders are strongest when reranking semantically rich text pairs,
  expected gains are moderate unless we enrich the retrieval corpus with detailed
  incident descriptions, work notes, and resolution narratives.
- Therefore, cross-encoder reranking is a good future enhancement, but not the first
  scaling lever for the present dataset shape.
