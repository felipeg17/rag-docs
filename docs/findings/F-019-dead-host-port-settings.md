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

`app_host`/`app_port` are unused because the Dockerfile CMD hardcodes `--port 8106`. `HOST`/`PORT` in the configmaps and `API_HOST`/`API_PORT` in the template are no-ops (`app_port` would read `APP_PORT`).

## Evidence

- `backend/app/core/config.py:89-90`
- `backend/Dockerfile:28`
- `k8s/base/backend/configmap*.yaml:10-11`
- `backend/backend.env.template:2-3`

## Impact

Misleading config; changing the port has no effect.

## Suggested fix

Pick one variable name and use it in the entrypoint.

## Follow-up

- [ ] Unify name
- [ ] Use it in Dockerfile CMD
