# F-013: Health checks do not reflect readiness

| Field | Value |
|---|---|
| Severity | Medium |
| Category | infrastructure |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

`/health` returns 200 even with `"database": "disconnected"` and never checks the vector DB. Readiness and liveness share the endpoint, readiness runs every 60s, no startupProbe.

## Evidence

- `backend/app/api/routers/health.py:12-18`
- `k8s/base/backend/deployment.yaml:39-51`

## Impact

Traffic routed to a pod that cannot serve; slow detection of failures.

## Suggested fix

Separate `/ready` (503 when dependencies down) and lightweight `/live`; add startupProbe; shorter readiness period.

## Follow-up

- [ ] Add endpoints
- [ ] Update deployment probes
