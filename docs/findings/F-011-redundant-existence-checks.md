# F-011: Duplicated and wasteful document existence checks

| Field | Value |
|---|---|
| Severity | Medium |
| Category | efficiency |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

pgvector `check_document_exists` runs an embedding call on `""` just to check existence. Ingestion checks twice (router then service), with a race between check and insert.

## Evidence

- `backend/app/infrastructure/vector_db/pgvector_repository.py:86-95`
- `backend/app/services/ingest/ingestion.py:43`
- `backend/app/api/routers/v1/document.py:57`

## Impact

Extra embedding API cost/latency per ingest; possible duplicate ingestion under concurrency.

## Suggested fix

Metadata-only `SELECT`; single check point; rely on a DB constraint (see F-002).

## Follow-up

- [ ] Metadata-only existence query
- [ ] Remove duplicate check
