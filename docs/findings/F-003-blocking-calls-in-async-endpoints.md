# F-003: Async endpoints perform blocking I/O

| Field | Value |
|---|---|
| Severity | High |
| Category | performance |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | #19 (related) |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

`ingest_document`, `search_document` and `ask_question` are `async def` but call sync SQLAlchemy, the Chroma HTTP client, embeddings, Cohere and `chain.invoke`.

## Evidence

- `backend/app/api/routers/v1/document.py:38,118,191`
- `k8s/base/backend/deployment.yaml:46-51 (liveness probe, default 1s timeout)`

## Impact

Blocks the event loop: concurrent requests serialize and `/health` stalls, so the liveness probe can kill the pod during long LLM calls.

## Suggested fix

Make the handlers plain `def` (FastAPI runs them in a threadpool) as a quick fix, or move to `ainvoke` + async clients.

## Follow-up

- [ ] Convert handlers to `def` or async clients
- [ ] Load test concurrent `/ask` + `/health`
