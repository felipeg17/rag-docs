# F-024: Interaction/document fields never populated; document_type mismatch

| Field | Value |
|---|---|
| Severity | Low |
| Category | correctness |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | #15 |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

`log_qa` never receives `llm_model`; `page_count` is never passed to `create_document`. `/ask` hardcodes `"documento-pdf"` while ingestion defaults to `"documento_pdf"` (underscore).

## Evidence

- `backend/app/api/routers/v1/document.py:49-54,213,222,241-248`
- `backend/app/services/ingest/ingestion.py:23`

## Impact

Incomplete analytics; filter mismatch if the ingestion default is ever used.

## Suggested fix

Pass the missing fields; make `document_type` an input with one canonical value.

## Follow-up

- [ ] Populate llm_model and page_count
- [ ] Unify document_type value
