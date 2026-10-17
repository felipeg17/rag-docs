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

## Notes

- 2026-10-17 (architect, SPEC-002): [SPEC-002](../specs/SPEC-002-web-frontend.md) removed `docker-compose.yaml` and `backend/backend.env.template` (user decision). The backend reads no env file (`config.py:92-96`), so the configmaps plus the `api-keys` secret (`k8s/base/backend/deployment.yaml:27-31`) are now the only source besides code defaults. The defect is unchanged and more relevant: `configmap.yaml` and `configmap-local.yaml` still lack `PGVECTOR_USER/PASSWORD/DATABASE/SCHEMA/TABLE` and `DB_SCHEMA` (re-read 2026-10-17). Status stays Open.
