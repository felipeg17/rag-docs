# F-006: Vertex AI embeddings path uses an OpenAI model name

| Field | Value |
|---|---|
| Severity | High |
| Category | correctness |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

With `USE_VERTEX_AI=true`, `VertexAIEmbeddings(model_name=settings.embeddings_model)` receives the default `text-embedding-ada-002`.

## Evidence

- `backend/app/core/config.py:48`
- `backend/app/infrastructure/embeddings/client.py:29-35`

## Impact

Vertex deployments fail (or require overriding a shared setting) for embeddings.

## Suggested fix

Add a dedicated `vertex_embeddings_model` setting (default `text-multilingual-embedding-002`).

## Follow-up

- [ ] Add setting
- [ ] Add unit test for the Vertex branch
