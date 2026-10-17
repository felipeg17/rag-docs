# F-033: No way to list uploaded documents (UI title is free text)

| Field | Value |
|---|---|
| Severity | Low |
| Category | api |
| Status | Open |
| Verification | Confirmed — 2026-10-16, architect, branch `spec/SPEC-002-web-frontend` (base `dev` @ `1fbb820`): `backend/app/api/routers/v1/document.py` declares only `POST` routes (`:28` ingest, `:109` search, `:182` ask); the only `GET` is `/health` (`backend/app/api/routers/health.py:12`). The offline OpenAPI dump lists 4 paths. The Ask page takes the title as free text (`frontend/components/chatbot.py:10`). |
| Tracking issue | — |
| Found | 2026-10-16 — [SPEC-002](../specs/SPEC-002-web-frontend.md) open question 2 |

## Problem

The API has no route that lists documents, so the UI cannot offer a document picker. Users must type the exact title they uploaded; a typo returns 404. SPEC-002 mitigates this only for titles uploaded in the current page session (`<datalist>` suggestions in memory).

## Evidence

- `backend/app/api/routers/v1/document.py:28,109,182`
- `backend/app/api/routers/health.py:12`

## Impact

Asking about a document uploaded in an earlier session, or by someone else, requires knowing its exact title.

## Suggested fix

A later spec: `GET /api/v1/documents` (repository and `DocumentService` list method, response model, unit tests, contract row), then a picker in the Ask view fed by it. Decide which store is the source of truth (Postgres registry or vector store; see [F-002](F-002-inconsistent-document-identity.md)).

## Follow-up

- [ ] List endpoint
- [ ] Document picker in the Ask view
