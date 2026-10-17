# F-020: PGVector port/host default differs from the k8s configmaps

| Field | Value |
|---|---|
| Severity | Low |
| Category | config |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

The code default is `localhost:6024`; both configmaps set `pgvector:5432`. 6024 only works through a port-forward to the pgvector Service: the skaffold one (`localPort: 6024`) or CI's `6024:5432`. Originally the env template also set `PGVECTOR_PORT=6024` with no `PGVECTOR_HOST`, relying on `network_mode: host` in docker-compose; both files are gone (see *Notes*).

## Evidence

- `backend/app/core/config.py:66-67`
- `k8s/base/backend/configmap*.yaml:8-9`
- `k8s/base/vectordb/pgvector/skaffold.yaml:28`
- `.github/workflows/integration-test.yml:127-128,137`

## Impact

Confusing local setup.

## Suggested fix

Document that the code default targets the port-forward and the configmaps target the in-cluster Service, or align them.

## Follow-up

- [ ] Document or align the default and docs/guides/setup.md

## Notes

- 2026-10-17 (architect, SPEC-002): `backend/backend.env.template` and `docker-compose.yaml` were removed by [SPEC-002](../specs/SPEC-002-web-frontend.md) (user decision; Kubernetes is the only run path). The template half of this finding (`backend.env.template:16`, no `PGVECTOR_HOST`, compose host networking) no longer exists; Problem, Evidence and title were narrowed. What remains: the code default `localhost:6024` (`config.py:66-67`) matches the port-forwards (`pgvector/skaffold.yaml:28`, `integration-test.yml:137`), while the configmaps set `pgvector:5432` (`configmap*.yaml:8-9`) for in-cluster use. That may now be intended rather than a defect; whether to close it is for the user. Status stays Open.
