# F-020: PGVector port/host mismatch between env template and k8s

| Field | Value |
|---|---|
| Severity | Low |
| Category | config |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

`PGVECTOR_PORT=6024` in the template and code default vs 5432 in both configmaps; 6024 only works via the CI port-forward `6024:5432`. The template has no `PGVECTOR_HOST`, relying on `network_mode: host` in docker-compose.

## Evidence

- `backend/backend.env.template:16`
- `backend/app/core/config.py:66-67`
- `k8s/base/backend/configmap*.yaml`

## Impact

Confusing local setup.

## Suggested fix

Document or align the values; add `PGVECTOR_HOST` to the template.

## Follow-up

- [ ] Align template and docs/guides/setup.md
