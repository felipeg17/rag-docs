# Overview

RAG-Docs: FastAPI backend for PDF ingestion + Retrieval-Augmented Generation.
Chunks PDFs, stores embeddings (ChromaDB or PGVector), and answers questions via LLM.

## Stack

- **Backend**: Python 3.10, FastAPI, LangChain, ChromaDB/PGVector, PostgreSQL, Alembic
- **Frontend**: Streamlit (`frontend/front.py`) — PDF upload + chatbot pages
- **Package manager**: `uv` (separate `pyproject.toml` in `backend/` and `frontend/`)
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

## Configuration

Each component has its own `.env` file (`backend/backend.env`, `frontend/frontend.env`) — copy from the `.env.template`. 
See `docs/SETUP.md` for all variables and LLM/vector DB options.

## Common Commands

```bash
# Tests
pytest tests/unit -v

# Lint / type check
ruff check app && ruff format app && mypy app

# Deploy (from repo root)
skaffold dev --profile local,ollama -f skaffold.yaml
```

## Documentation

- `docs/ARCHITECTURE.md` — service details, DB schema, LLM providers, DI flow
- `docs/SETUP.md` — env vars, local dev, Kubernetes/Skaffold setup
- `docs/TESTING.md` — test structure, CI/CD
- `docs/CONTRIBUTING.md` — branching, code style, PR process
- `k8s/README.md` — minikube cluster setup and Skaffold profiles
