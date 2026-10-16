# F-017: Secrets and credentials handling

| Field | Value |
|---|---|
| Severity | Medium |
| Category | security |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

Default DB credentials `langchain/langchain` are hardcoded in Settings and as plain env values in k8s. A missing local secret makes `get_secret` return `""`, so OpenAI/Cohere clients are built with empty keys and fail only at request time. `lru_cache` keeps secrets for the process lifetime. `get_secret` logs the full exception at info level.

## Evidence

- `backend/app/core/config.py:67-70`
- `k8s/base/vectordb/pgvector/deployment.yaml:25-30`
- `backend/app/core/helpers.py:46-53,67`

## Impact

Weak defaults, late failures, possible secret-adjacent data in logs.

## Suggested fix

Move DB credentials to a k8s Secret; fail at startup when a required key is missing; log at warning without exception detail.

## Follow-up

- [ ] k8s Secret for pgvector
- [ ] Required-key validation at startup
