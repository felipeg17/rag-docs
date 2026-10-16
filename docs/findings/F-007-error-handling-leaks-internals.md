# F-007: Error handling leaks internals and returns wrong status codes

| Field | Value |
|---|---|
| Severity | Medium |
| Category | security |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

500 responses include `type(e).__name__ - str(e)`, which can expose DB URLs or provider errors. A corrupt PDF raises `ValueError` and returns 500 instead of 400/422.

## Evidence

- `backend/app/api/routers/v1/document.py:99-105,172-178,261-267`
- `backend/app/services/document/pdf_loader.py:38`

## Impact

Information disclosure; clients cannot distinguish bad input from server faults.

## Suggested fix

Map domain errors to 4xx; return a generic 500 detail and log the exception server-side.

## Follow-up

- [ ] Define domain exceptions
- [ ] Exception handlers in the router/app
