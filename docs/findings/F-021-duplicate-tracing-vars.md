# F-021: Duplicate LangChain/LangSmith tracing variables

| Field | Value |
|---|---|
| Severity | Low |
| Category | config |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

The env template set both `LANGCHAIN_*` and `LANGSMITH_*`; configmaps only `LANGCHAIN_TRACING_V2`/`LANGCHAIN_PROJECT`. The template was removed (see *Notes*).

## Evidence

- `backend/backend.env.template:7-13` (removed 2026-10-17; `dev` @ `1fbb820`)
- `k8s/base/backend/configmap*.yaml:12-13`
- `.github/workflows/submission-check.yml:175`

## Impact

Unclear which variables take effect.

## Suggested fix

Standardize on `LANGSMITH_*`.

## Follow-up

- [ ] Clean template and configmaps

## Notes

- 2026-10-17 (architect, SPEC-002): `backend/backend.env.template` was removed by [SPEC-002](../specs/SPEC-002-web-frontend.md) (user decision; Kubernetes is the only run path). No `LANGSMITH_*` variable remains in `k8s/`, `.github/` or `docs/guides/`; only `LANGCHAIN_PROJECT`/`LANGCHAIN_TRACING_V2` (`configmap*.yaml:12-13`) and `LANGCHAIN_PROJECT` (`submission-check.yml:175`). The installed langsmith 0.4.4 reads each setting as `LANGSMITH_<name>` first, then `LANGCHAIN_<name>` (`langsmith/utils.py:368-392`), and tracing as `TRACING_V2`, then `TRACING` (`utils.py:114`), so the remaining `LANGCHAIN_*` names take effect. The duplication this finding describes is gone; the "Standardize on `LANGSMITH_*`" follow-up is optional hygiene. Whether to close it is for the user. Status stays Open.
