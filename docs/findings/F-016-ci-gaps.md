# F-016: CI and test coverage gaps

| Field | Value |
|---|---|
| Severity | Medium |
| Category | ci |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

CI runs only `ruff format --check`, never `ruff check`. Frontend has no mypy or tests. Integration tests only run `skaffold run -p ci,chroma`, so pgvector is never exercised end to end. No unit tests for `pgvector_repository.py`, `pgvector_client.py`, `dependencies.py`, `lifespan.py`; QA/rerank service tests (2 each) don't cover filtering or context formatting.

## Evidence

- `.github/workflows/submission-check.yml:66-97`
- `.github/workflows/integration-test.yml:120`
- `backend/tests/unit/`

## Impact

Bugs like F-001, F-004, F-005 ship undetected.

## Suggested fix

Add `ruff check`, a pgvector integration matrix entry, and the missing unit tests.

## Follow-up

- [ ] `ruff check` in CI
- [ ] pgvector integration run
- [ ] Unit tests for pgvector repo/client, DI, lifespan
