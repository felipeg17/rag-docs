# F-005: `get_vector_size` returns wrong or silently defaulted dimensions

| Field | Value |
|---|---|
| Severity | High |
| Category | correctness |
| Status | Open |
| Verification | Confirmed — manually checked against source |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

`nomic-embed-text-v2-moe` is hardcoded to 256 dims, but local Ollama reports `embedding_length: 768` for that model and nothing tells `OllamaEmbeddings` to truncate. Unknown models silently fall back to 768 (e.g. `text-embedding-3-small` = 1536, plain `nomic-embed-text` tag missing). `init_vectorstore_table` errors are logged and swallowed, so a model switch leaves a table with the wrong dimension that only fails on insert. The unit test pins the 256 value.

## Evidence

- `backend/app/core/config.py:98-117`
- `backend/app/infrastructure/vector_db/pgvector_repository.py:27-38`
- `backend/tests/unit/infrastructure/config_test.py:7-9`
- `curl localhost:11434/api/tags` → nomic-embed-text-v2-moe embedding_length 768

## Impact

pgvector + `LOCAL_LLM=true` (default Ollama embeddings) creates a 256-dim table; inserts of 768-dim vectors fail.

## Suggested fix

Measure `len(embeddings.embed_query("x"))` at startup and validate it against the existing table, or raise on unknown models. Fix the 256 entry and the test.

## Follow-up

- [ ] Fix dimension map / probe at startup
- [ ] Fail fast on table dimension mismatch
- [ ] Update config_test
