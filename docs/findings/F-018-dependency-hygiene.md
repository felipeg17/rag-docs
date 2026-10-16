# F-018: Undeclared, unused and unpinned dependencies

| Field | Value |
|---|---|
| Severity | Medium |
| Category | dependencies |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

`sqlalchemy` (imported in 10 files) and `psycopg` (via `postgresql+psycopg` URL) are not declared — only transitive. `boto3`, `botocore`, `langchain-aws`, `langchain-google-genai`, `httpx-sse`, `tokenizers` are declared but never imported under `backend/app`. `langchain-postgres` and `langchain-ollama` use `>=` while everything else is pinned.

## Evidence

- `backend/pyproject.toml:7-54`

## Impact

Fragile installs if a transitive dep changes; larger images.

## Suggested fix

Declare direct deps, remove unused ones (confirm Bedrock work is abandoned first), pin consistently.

## Follow-up

- [ ] Confirm Bedrock/genai not needed
- [ ] Update pyproject + uv.lock
