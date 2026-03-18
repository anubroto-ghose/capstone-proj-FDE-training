# Submission Readiness Checklist

## Current Status

### Requirement 1 (Basic)
- [x] Basic RAG for incident similarity search
- [x] Hybrid search (keywords + semantic)
- [x] Triage agent for priority classification
- [x] Metadata filtering (priority, impact, category)
- [x] Basic resolution suggestion
- [x] Input validation guardrails
- [x] Simple ticket routing
- [x] API endpoint exposure

### Requirement 2 (Advanced)
- [x] DeepEval integration (baseline test present)
- [x] Custom metrics (resolution time prediction, fix accuracy)
- [x] Rerank by recency and resolution success signal
- [x] LLM-as-judge validation tool
- [x] Token optimization for long context
- [x] Multi-tier L1 -> L2 -> L3 handoff
- [x] A2A knowledge sharing
- [x] Root cause analysis agent collaboration
- [x] Feedback loop
- [x] Frontend interface

## Deliverables Status
- [x] Design decisions and trade-offs documented (`docs/architecture_and_design.md`)
- [x] Full executable code (microservices + frontend)
- [x] Root README with setup and sample usage
- [ ] Architecture diagram exported to JPEG/PDF (Mermaid exists, export pending)
- [ ] Panel deck and 10-minute demo script finalized

## Improvements Completed In This Pass
- Retrieval now enriches search results with incident resolution context:
  - `status`
  - `closure_code`
  - `related_change`
  - `resolved_time`
  - `resolution_summary`
- Chat request model now enforces:
  - minimum and maximum message length
  - whitespace normalization
  - non-empty input validation
- L1/L2 prompts now explicitly require citing incident IDs and resolution summaries.

## Final Pre-Submission Tasks
1. Export architecture Mermaid diagram to `docs/architecture_diagram.pdf` or `.jpeg`.
2. Add 3-5 realistic DeepEval cases (network, DB timeout, auth, memory leak, remote access denial).
3. Prepare a fixed demo flow:
   - Login
   - New incident query
   - Hybrid retrieval evidence shown
   - L1 to L2 handoff example
   - Feedback submission
4. Add one short section in README with:
   - service start order
   - required `.env` keys per service
   - expected sample API response payload.
