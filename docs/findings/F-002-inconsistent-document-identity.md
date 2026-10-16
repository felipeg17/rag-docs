# F-002: Postgres and vector DB deduplicate on different keys

| Field | Value |
|---|---|
| Severity | High |
| Category | correctness |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | #20 |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

Postgres deduplicates by content hash (unique), the router/vector DB by title (indexed, not unique). Same PDF + new title: Postgres returns the old row while chunks are ingested again; later `get_by_title(new_title)` returns None and interactions are silently not logged. Different PDF + existing title: a second Postgres row is created, ingestion is skipped, and `get_by_title` raises `MultipleResultsFound` (`scalar_one_or_none`) → `/search` and `/ask` return 500 after the LLM already ran.

## Evidence

- `backend/app/services/persistence/document_service.py:32`
- `backend/app/infrastructure/database/models.py:58,62-64`
- `backend/app/api/routers/v1/document.py:57`
- `backend/app/infrastructure/database/repositories/document_repository.py:17,22`

## Impact

Duplicate chunks, missing interaction logs, and 500 errors depending on ingest order.

## Suggested fix

Choose a single identity (document UUID or content hash), route endpoints by it (or make title unique), and store `document_id` in chunk metadata.

## Follow-up

- [ ] Decide canonical document identity
- [ ] Migration (Alembic) for uniqueness constraint
- [ ] Store document_id in chunk metadata
