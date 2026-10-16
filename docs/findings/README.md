# Findings

Tracked improvement opportunities and defects. Each finding is one file so it can map 1:1 to a GitHub issue.

## Workflow

1. **Record**: copy an existing finding as a template; use the next free `F-NNN` id. Never reuse ids.
2. **Track**: open a GitHub issue, link it in the finding's *Tracking issue* field and in the table below.
   To fix it, run `/spec new F-NNN` (see [specs](../specs/README.md)).
3. **Resolve**: `qa-agent` sets *Status* to `Fixed (SPEC-NNN)` when the spec is verified, or the user sets `Fixed` (with PR link) or `Won't fix` (with reason). Keep the file for history.

| Field | Values |
|---|---|
| Severity | `High` (wrong results / outages) · `Medium` (quality, security, CI gaps) · `Low` (hygiene, consistency) |
| Status | `Open` · `In progress` · `Fixed` · `Won't fix` |
| Verification | `Confirmed` (manually checked or reproduced) · `Reported` (found by code reading, verify before fixing) |

## Index

| ID | Title | Severity | Category | Status | Issue |
|---|---|---|---|---|---|
| [F-001](F-001-retrieval-not-scoped-to-document.md) | Retrieval is not scoped to the requested document | High | correctness | Open | — |
| [F-002](F-002-inconsistent-document-identity.md) | Postgres and vector DB deduplicate on different keys | High | correctness | Open | #20 |
| [F-003](F-003-blocking-calls-in-async-endpoints.md) | Async endpoints perform blocking I/O | High | performance | Open | #19 (related) |
| [F-004](F-004-rerank-context-not-formatted.md) | Rerank chain injects raw `list[Document]` into the prompt | High | rag-quality | Open | — |
| [F-005](F-005-wrong-vector-size.md) | `get_vector_size` returns wrong or silently defaulted dimensions | High | correctness | Open | — |
| [F-006](F-006-vertex-embeddings-model-name.md) | Vertex AI embeddings path uses an OpenAI model name | High | correctness | Open | — |
| [F-007](F-007-error-handling-leaks-internals.md) | Error handling leaks internals and returns wrong status codes | Medium | security | Open | — |
| [F-008](F-008-rerank-near-noop.md) | Rerank is close to a no-op and returns no sources | Medium | rag-quality | Open | — |
| [F-009](F-009-weak-chunking.md) | Chunking strategy is weak | Medium | rag-quality | Open | — |
| [F-010](F-010-prompt-grounding.md) | Prompt lacks grounding fallback; prompt load failures are silent | Medium | rag-quality | Open | — |
| [F-011](F-011-redundant-existence-checks.md) | Duplicated and wasteful document existence checks | Medium | efficiency | Open | — |
| [F-012](F-012-chroma-only-where-document.md) | Chroma-only `where_document` leaks into shared code | Medium | correctness | Open | — |
| [F-013](F-013-health-checks.md) | Health checks do not reflect readiness | Medium | infrastructure | Open | — |
| [F-014](F-014-startup-not-fail-fast.md) | Startup does not fail fast; engines not disposed | Medium | reliability | Open | — |
| [F-015](F-015-coverage-upload-empty.md) | Codecov upload has no coverage report | Medium | ci | Open | — |
| [F-016](F-016-ci-gaps.md) | CI and test coverage gaps | Medium | ci | Open | — |
| [F-017](F-017-secrets-handling.md) | Secrets and credentials handling | Medium | security | Open | — |
| [F-018](F-018-dependency-hygiene.md) | Undeclared, unused and unpinned dependencies | Medium | dependencies | Open | — |
| [F-019](F-019-dead-host-port-settings.md) | Host/port settings are never used | Low | config | Open | — |
| [F-020](F-020-pgvector-port-host-mismatch.md) | PGVector port/host mismatch between env template and k8s | Low | config | Open | — |
| [F-021](F-021-duplicate-tracing-vars.md) | Duplicate LangChain/LangSmith tracing variables | Low | config | Open | — |
| [F-022](F-022-configmaps-out-of-sync.md) | Configmaps out of sync with Settings | Low | config | Open | — |
| [F-023](F-023-mislabelled-path-params.md) | `document_id` path param is actually a title; Location header points nowhere | Low | api | Open | — |
| [F-024](F-024-unwritten-logged-fields.md) | Interaction/document fields never populated; document_type mismatch | Low | correctness | Open | #15 |
| [F-025](F-025-deprecated-langchain-usage.md) | Deprecated LangChain APIs; chains rebuilt per request | Low | maintenance | Open | #16 (related) |
| [F-026](F-026-docker-hygiene.md) | Docker image hygiene and Python 3.10 EOL | Low | infrastructure | Open | — |
| [F-027](F-027-k8s-resources-availability.md) | K8s resource requests, replicas and frontend probes | Low | infrastructure | Open | — |
| [F-028](F-028-frontend-requests.md) | Frontend HTTP calls: no URL encoding, timeout or error handling | Low | frontend | Open | — |
| [F-029](F-029-frontend-ux-security.md) | Frontend UX and security settings | Low | frontend | Open | — |
| [F-030](F-030-misnamed-init-file.md) | `__initi__.py` typo in repositories package | Low | maintenance | Open | — |

## Audits

### 2026-10-15 — Repository audit

- **Scope**: `backend/app`, `frontend/`, `k8s/`, `.github/workflows`, config templates. Read-only code review; no tests executed, cluster not running.
- **Baseline**: `dev` @ `d328566` (identical tree to `origin/main` @ `1698aa8`).
- **Config at time of audit** (code defaults; no `backend.env` present):

| Mode | LLM | Embeddings | Vector DB |
|---|---|---|---|
| `local` profile (`LOCAL_LLM=true`) | Ollama `qwen3:8b` | Ollama `nomic-embed-text-v2-moe` | Chroma |
| Default configmap (OpenAI) | `gpt-4.1-nano` | `text-embedding-ada-002` | Chroma |
| `USE_VERTEX_AI=true` | `gemini-2.5-flash` | `text-embedding-ada-002` (see F-006) | Chroma |
| `backend.env.template` | OpenAI | `text-embedding-ada-002` | pgvector |

Retrieval defaults: chunk 800 / overlap 50 chars, k=4, Cohere `rerank-v3.5` top_n=3, temperature 0.05, top_p 0.1.

**Suggested order**: F-001, F-002 (data correctness) → F-004, F-005 → F-003.
