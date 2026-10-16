# F-026: Docker image hygiene and Python 3.10 EOL

| Field | Value |
|---|---|
| Severity | Low |
| Category | infrastructure |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

`ghcr.io/astral-sh/uv:latest` unpinned in both Dockerfiles; containers run as root; no `HEALTHCHECK`. `requires-python <3.11` pins Python 3.10, which reaches end of life in October 2026.

## Evidence

- `backend/Dockerfile`
- `frontend/Dockerfile`
- `backend/pyproject.toml:5`

## Impact

Non-reproducible builds; unsupported runtime.

## Suggested fix

Pin uv image; non-root user; plan upgrade to Python 3.12+.

## Follow-up

- [ ] Pin uv
- [ ] Non-root user
- [ ] Python upgrade plan
