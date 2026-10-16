# F-001: Retrieval is not scoped to the requested document

| Field | Value |
|---|---|
| Severity | High |
| Category | correctness |
| Status | Open |
| Verification | Confirmed — manually checked against source |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

`/ask` validates that the document title exists, but the retriever only filters on `tipo_documento`, so answers can draw on chunks from every ingested PDF. In `/search`, `metadata_filter` defaults to `{}` (falsy), so `metadata_filter or {...}` falls back to the type-only filter and `titulo` is never applied. `QuestionRequest.metadata_filter` is accepted but never used.

## Evidence

- `backend/app/services/rag/qa_service.py:59`
- `backend/app/services/rag/rerank_service.py:69`
- `backend/app/infrastructure/vector_db/repository.py:54`
- `backend/app/infrastructure/vector_db/pgvector_repository.py:68`
- `backend/app/models/requests/search_request.py:9,18`

## Impact

Answers and sources may come from unrelated documents; results are wrong as soon as more than one PDF is ingested.

## Suggested fix

Always include the document identity in the filter (Chroma `$and`, pgvector metadata filter). Use `if metadata_filter is None`. Pass `QuestionRequest.metadata_filter` through to the services.

## Follow-up

- [ ] Add document filter to QA and rerank retrievers
- [ ] Fix `/search` default filter handling
- [ ] Unit tests asserting the filter contains the document id
