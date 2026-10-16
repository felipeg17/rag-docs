# F-030: `__initi__.py` typo in repositories package

| Field | Value |
|---|---|
| Severity | Low |
| Category | maintenance |
| Status | Open |
| Verification | Confirmed — manually checked against source |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

`repositories/__initi__.py` should be `__init__.py`.

## Evidence

- `backend/app/infrastructure/database/repositories/__initi__.py`

## Impact

Package works only as a namespace package; tooling may behave inconsistently.

## Suggested fix

`git mv __initi__.py __init__.py`.

## Follow-up

- [ ] Rename file
