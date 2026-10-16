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

The template sets both `LANGCHAIN_*` and `LANGSMITH_*`; configmaps only `LANGCHAIN_TRACING_V2`/`LANGCHAIN_PROJECT`.

## Evidence

- `backend/backend.env.template:7-13`
- `k8s/base/backend/configmap*.yaml`

## Impact

Unclear which variables take effect.

## Suggested fix

Standardize on `LANGSMITH_*`.

## Follow-up

- [ ] Clean template and configmaps
