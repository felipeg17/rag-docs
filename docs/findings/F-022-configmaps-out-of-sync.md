# F-022: Configmaps out of sync with Settings

| Field | Value |
|---|---|
| Severity | Low |
| Category | config |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

Configmaps lack `PGVECTOR_USER/PASSWORD/DATABASE/SCHEMA/TABLE` and `DB_SCHEMA`. The `config.py:10` comment asks to keep them in sync but nothing enforces it.

## Evidence

- `k8s/base/backend/configmap.yaml`
- `k8s/base/backend/configmap-local.yaml`
- `backend/app/core/config.py:10`

## Impact

Silent reliance on code defaults.

## Suggested fix

Add missing keys (secrets via Secret) and a unit test that compares Settings fields with configmap keys.

## Follow-up

- [ ] Sync configmaps
- [ ] Drift test
