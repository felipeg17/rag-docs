# F-019: Host/port settings are never used

| Field | Value |
|---|---|
| Severity | Low |
| Category | config |
| Status | Open |
| Verification | Confirmed — manually checked against source |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

`app_host`/`app_port` are unused because the Dockerfile CMD hardcodes `--port 8106`. `HOST`/`PORT` in the configmaps are no-ops (`app_port` would read `APP_PORT`). The env template's `API_HOST`/`API_PORT` were no-ops too; the template was removed (see *Notes*).

## Evidence

- `backend/app/core/config.py:89-90`
- `backend/Dockerfile:28`
- `k8s/base/backend/configmap*.yaml:10-11`

## Impact

Misleading config; changing the port has no effect.

## Suggested fix

Pick one variable name and use it in the entrypoint.

## Follow-up

- [ ] Unify name
- [ ] Use it in Dockerfile CMD

## Notes

- 2026-10-17 (architect, SPEC-002): `backend/backend.env.template` and `docker-compose.yaml` were removed by [SPEC-002](../specs/SPEC-002-web-frontend.md) (user decision; Kubernetes is the only run path). The template evidence (`backend.env.template:2-3`, `API_HOST`/`API_PORT`) is dropped. The defect remains: re-read `config.py:89-90` (`app_host` reads `HOST`, `app_port` has no alias and is unused), `backend/Dockerfile:28` (`--port 8106` hard-coded) and `k8s/base/backend/configmap*.yaml:10-11` (`HOST`, `PORT`). Status stays Open.
