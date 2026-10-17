# Overview

RAG-Docs: FastAPI backend for PDF ingestion + Retrieval-Augmented Generation.
Chunks PDFs, stores embeddings (ChromaDB or PGVector), and answers questions via LLM.
A web UI uploads PDFs and asks questions about them.

## Stack

- **Backend**: Python 3.10, FastAPI, LangChain, ChromaDB/PGVector, PostgreSQL, Alembic
- **Frontend**: Vite + React 19 + TypeScript (strict), CSS modules, Biome, vitest (`frontend/src/`).
  Two views, Upload and Ask; UI copy is Spanish. Served by nginx-unprivileged on port 8502,
  which proxies `/api` to the backend same-origin (`frontend/nginx/default.conf.template`)
- **API types**: generated from the backend's committed `backend/openapi.json` into
  `frontend/src/api/openapi_gen.ts` (never hand-edited)
- **Package managers**: `uv` in `backend/`, npm in `frontend/` (Node 24)
- **Deployment**: Kubernetes via Skaffold + minikube

## Architecture

FastAPI Dependency Injection (`app/core/dependencies.py`) wires everything:

```
HTTP Request
    ↓
Singletons (cached):  get_llm_client, get_embeddings_client, get_vector_db_repository, get_db_client
    ↓
Request-scoped:       get_db_session → get_document_repository → get_document_service
                      get_db_session → get_*_interaction_repository → get_interaction_service
    ↓
Endpoint handler
```

## Services

| Service | File | Responsibility |
|---------|------|----------------|
| `DocumentIngestionService` | `services/ingest/ingestion.py` | PDF → decode → extract → chunk → embed → store |
| `QAService` | `services/rag/qa_service.py` | Retrieve + LLM answer (returns answer + sources) |
| `RerankService` | `services/rag/rerank_service.py` | Retrieve → Cohere rerank → LLM |
| `DocumentService` | `services/persistence/document_service.py` | PostgreSQL registry, SHA-256 deduplication |
| `InteractionService` | `services/persistence/interaction_service.py` | Logs all search/QA calls |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/documents` | Ingest PDF (base64 in body) |
| POST | `/api/v1/documents/{document_id}/search` | Similarity search |
| POST | `/api/v1/documents/{document_id}/ask` | Q&A (`strategy`: `standard` or `rerank`) |

The web UI calls these same-origin through its nginx (or the Vite dev proxy): `/api/v1/*` as is,
`/health` as `/api/health`. See `docs/reference/architecture.md` § Frontend.

## Configuration

There are no env files. Kubernetes (Skaffold + minikube) is the only way to run the stack.

- **Backend**: process environment variables, else the defaults in `backend/app/core/config.py` (no `env_file`).
  In Kubernetes they come from the `backend-config` configmap (`k8s/base/backend/configmap.yaml`;
  `configmap-local.yaml` with the `local` profile) and the `api-keys` secret (`OPENAI_API_KEY`, `COHERE_API_KEY`).
- **Frontend**: the nginx upstream (`API_HOST`, `API_PORT`) comes from `k8s/base/frontend/configmap.yaml`;
  `npm run dev` proxies to `API_PROXY_TARGET` (default `http://localhost:8106`).

See `docs/guides/setup.md` for all variables and LLM/vector DB options.

## Common Commands

```bash
# Backend (in backend/)
pytest tests/unit -v
ruff check app && ruff format app && mypy app
uv run python export_openapi.py   # after an API model change: regenerate openapi.json

# Frontend (in frontend/, after npm ci)
npm run dev                       # :5173, proxies /api to http://localhost:8106
npm run gen:api                   # after export_openapi.py: regenerate src/api/openapi_gen.ts
npm run check:api && npm run lint && npm run typecheck && npm test && npm run build

# Deploy (from repo root)
skaffold dev --profile local,ollama -f skaffold.yaml
```

## Documentation

- `docs/reference/architecture.md` — service details, DB schema, LLM providers, DI flow
- `docs/guides/setup.md` — env vars, local dev, Kubernetes/Skaffold setup
- `docs/development/testing.md` — test structure, CI/CD
- `docs/development/contributing.md` — branching, code style, PR process
- `docs/findings/` — tracked defects/improvements (one file per finding, `F-NNN`)
- `docs/specs/` — specs (`SPEC-NNN`); product changes follow the `/spec` pipeline (see `.claude/CLAUDE.md`)
- `k8s/README.md` — minikube cluster setup and Skaffold profiles
