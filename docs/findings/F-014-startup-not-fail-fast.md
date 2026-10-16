# F-014: Startup does not fail fast; engines not disposed

| Field | Value |
|---|---|
| Severity | Medium |
| Category | reliability |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

A DB heartbeat failure is only logged; the Chroma `heartbeat()` raises without handling (inconsistent with pgvector). Engines are never disposed on shutdown although `dispose()` exists.

## Evidence

- `backend/app/core/lifespan.py:26-37`

## Impact

Pods report healthy while broken; connection leaks on shutdown.

## Suggested fix

Consistent dependency checks with explicit failure; call `dispose()` in lifespan shutdown.

## Follow-up

- [ ] Unify startup checks
- [ ] Dispose engines on shutdown
