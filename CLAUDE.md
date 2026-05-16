# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RAG-Docs is a FastAPI-based backend for Retrieval-Augmented Generation (RAG) with PDF document processing. The system ingests PDF documents, splits them into chunks, stores embeddings in a vector database (ChromaDB or PGVector), and provides search/question-answering APIs with standard RAG or reranking strategies.

## Running the Application

### Docker Compose (Recommended)

```bash
# Start all services (backend + frontend)
docker compose --env-file image.env --profile full up --build

# Start only backend
docker compose --profile backend up --build

# Stop services
docker compose down
```

### Makefile shortcuts

```bash
make up           # Start all services
make up-backend   # Start only backend
make down         # Stop services
make build        # Build images
make rebuild      # Rebuild with no-cache
make logs         # View logs
make prune        # Prune Docker system
```

### Local Backend Development

The project uses `uv` as the package manager (`uv.lock` is checked in).

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload
```

## Environment Variables

Copy `backend/backend.env.template` to `backend/backend.env`. Key variables:

| Variable | Description |
|----------|-------------|
| `LOCAL_LLM` | `true` → Ollama; `false` → cloud LLM |
| `USE_VERTEX_AI` | `true` → Vertex AI (only when `LOCAL_LLM=false`) |
| `VECTOR_DB_TYPE` | `chroma` (default) or `pgvector` |
| `USE_SECRETS` | `true` → GCP Secret Manager for API keys; `false` → env vars |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_EMBEDDINGS_MODEL` | Ollama config |
| `OPENAI_API_KEY`, `COHERE_API_KEY` | Used when `USE_SECRETS=false` |

**LLM provider selection** (in `app/infrastructure/llm/client.py` and `embeddings/client.py`):
- `LOCAL_LLM=true` → Ollama (default model: `qwen3:8b`, embeddings: `nomic-embed-text-v2-moe`)
- `LOCAL_LLM=false` + `USE_VERTEX_AI=true` → Vertex AI (model: `gemini-2.5-flash`)
- `LOCAL_LLM=false` + `USE_VERTEX_AI=false` → OpenAI (model: `gpt-4.1-nano`)

## Testing

All test commands run from `backend/`:

```bash
# Unit tests
pytest tests/unit -v                    # All unit tests
pytest tests/unit/api -v               # API tests only
pytest tests/unit/services -v          # Service tests only
pytest tests/unit/services/rag/qa_service_test.py::TestClass::test_name -v  # Single test

# Integration tests (BDD) - requires a live backend at BACKEND_URL (default: http://localhost:8106)
BACKEND_URL=http://localhost:8106 behave tests/behave -v

# Lint & format
ruff check app
ruff format app

# Type check
mypy app
```

Integration tests run against a real backend; they are not run in CI on every PR — only when the `integration-tests` label is applied or on pushes to `main`.

Golden response fixtures live in `backend/tests/fixtures/golden_responses/` and are loaded by unit tests for mocking.

## Architecture

### Dependency Injection Flow

FastAPI DI (`backend/app/core/dependencies.py`) wires the entire application. Singletons are `@lru_cache`-decorated; request-scoped objects are plain functions:

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

### Service Layer

- **DocumentIngestionService** (`services/ingest/ingestion.py`): PDF → base64 decode → text extraction → chunking → vector DB store
- **QAService** (`services/rag/qa_service.py`): retrieval + LLM answering (returns answer + source docs)
- **RerankService** (`services/rag/rerank_service.py`): retrieval → Cohere rerank → LLM (returns answer only)
- **DocumentService** (`services/persistence/document_service.py`): PostgreSQL document registry with SHA-256 content-hash deduplication
- **InteractionService** (`services/persistence/interaction_service.py`): logs every search/QA call to PostgreSQL

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/documents` | Ingest PDF (base64-encoded in request body) |
| POST | `/api/v1/documents/{document_id}/search` | Similarity search |
| POST | `/api/v1/documents/{document_id}/ask` | Q&A (standard or rerank strategy) |

**Important**: `{document_id}` in the search and ask endpoints is the document **title** (not a UUID). It is used as a ChromaDB metadata filter (`{"titulo": title}`).

### Vector Database

- **ChromaDB** (default): HTTP client with tenant/database/collection isolation. Run `backend/admin_chroma.py` once to create the ChromaDB tenant and database before first use.
- **PGVector**: PostgreSQL + pgvector extension. Uses two schemas: `app` (application tables, managed by Alembic) and `vector` (embeddings, managed by LangChain).

Switch via `VECTOR_DB_TYPE` env var.

### Database Migrations (Alembic)

Run from `backend/`:

```bash
alembic current           # Show current migration version
alembic upgrade head      # Apply all pending migrations
alembic downgrade -1      # Rollback one version
alembic revision --autogenerate -m "description"  # Generate migration from model changes
```

Migrations are in `backend/app/migrations/versions/`. Always review auto-generated migrations before applying. The `app` schema tables (`documents`, `search_interactions`, `qa_interactions`) are managed here; the `vector` schema is managed by LangChain.

### Text Splitting

Configured via `TextSplitterFactory` (`services/document/text_splitter.py`):
- `"recursive"`: `RecursiveCharacterTextSplitter` — default, configurable chunk size/overlap
- `"semantic"`: `SemanticChunker` — embedding-based boundary detection (slower, requires embeddings call)

Currently the ingest endpoint hardcodes `"recursive"` (tracked as TODO).

## Frontend

Streamlit-based UI at `frontend/front.py` with two pages: PDF upload (ingestion) and chatbot (Q&A). Start with Docker Compose `--profile full`.
