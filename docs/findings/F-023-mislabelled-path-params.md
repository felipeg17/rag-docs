# F-023: `document_id` path param is actually a title; Location header points nowhere

| Field | Value |
|---|---|
| Severity | Low |
| Category | api |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

`document_id` is used as a title (described as "Document title"). The `Location` header points to `/api/v1/documents/{uuid}` but no GET route exists.

## Evidence

- `backend/app/api/routers/v1/document.py:92,119,192`

## Impact

Confusing API contract.

## Suggested fix

Resolve together with F-002 (route by UUID) and add `GET /documents/{id}`.

## Follow-up

- [ ] Rename/route by id
- [ ] Add GET endpoint
