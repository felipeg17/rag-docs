# F-012: Chroma-only `where_document` leaks into shared code

| Field | Value |
|---|---|
| Severity | Medium |
| Category | correctness |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

`{"$contains": " "}` is passed to `as_retriever` for both backends; its effect on PGVectorStore is unverified. The Chroma repo also forces it as a default.

## Evidence

- `backend/app/services/rag/qa_service.py:60`
- `backend/app/services/rag/rerank_service.py:70`
- `backend/app/infrastructure/vector_db/repository.py:57`

## Impact

Backend-specific behavior in services; possible errors or ignored kwargs on pgvector.

## Suggested fix

Move backend-specific search kwargs into each repository implementation.

## Follow-up

- [ ] Verify pgvector behavior
- [ ] Push kwargs into repositories
