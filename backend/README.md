# Backend

FastAPI-based server for document ingestion and RAG-powered question answering.

## Overview

The backend provides REST APIs for:
- **Document ingestion**: Upload PDFs, extract text, chunk, and embed
- **Search**: Semantic similarity search on document chunks
- **Question answering**: Retrieve relevant chunks and generate answers via LLM
- **Reranking**: Retrieve → rerank with Cohere → answer (alternative strategy)

After changing an API model or route, regenerate the OpenAPI snapshot with `uv run python export_openapi.py` (in `backend/`), then `npm run gen:api` (in `frontend/`).

## Quick Start

### Kubernetes (full stack)

From the repo root (Kubernetes via Skaffold is the only supported way to run the full stack):

```bash
skaffold dev -p local,chroma -f skaffold.yaml --port-forward
```

Backend runs at `http://localhost:8106`.

### Local Development

```bash
python -m venv .venv
source .venv/bin/activate
uv pip install -e .

# Initialize databases (if using ChromaDB)
python admin_chroma.py

# Or run migrations (if using PGVector)
alembic upgrade head

# Start server (overrides are plain env vars)
LOCAL_LLM=true VECTOR_DB_TYPE=chroma uvicorn main:app --reload --host 0.0.0.0 --port 8106
```

There is no env file: `Settings` (`app/core/config.py`) reads process environment variables only
and falls back to code defaults. Export overrides in the shell. Reference values live in
`../k8s/base/backend/configmap.yaml` and `configmap-local.yaml`.

Server runs at `http://localhost:8106`.

## API Endpoints

Full interactive documentation is available at `http://localhost:8106/docs` (Swagger UI) or `/redoc` (ReDoc) when the server is running.

### Health Check

```
GET /health
```

### Ingest Document

```
POST /api/v1/documents
```

Request body (`DocumentIngestRequest`):

```json
{
  "title": "my-document",
  "document_type": "documento-pdf",
  "document_content": "<base64-encoded-pdf>"
}
```

`document_type` is optional and defaults to `"documento-pdf"`. `document_content` must be a valid base64 string.

Response (`DocumentIngestResponse`):

```json
{
  "document_id": "uuid",
  "title": "my-document",
  "status": "created",
  "message": "Document created successfully"
}
```

`status` is `"created"` for new documents or `"updated"` if the document was re-uploaded.

### Search Documents

```
POST /api/v1/documents/{document_id}/search
```

`document_id` is the document **title** (not UUID).

Request body (`DocumentSearchRequest`):

```json
{
  "query": "what is RAG?",
  "k_results": 4,
  "metadata_filter": {}
}
```

`k_results` controls how many chunks to retrieve (1–10, default 4). `metadata_filter` can narrow results by chunk metadata.

Response (`DocumentSearchResponse`):

```json
{
  "query": "what is RAG?",
  "results": [
    {
      "content": "RAG stands for Retrieval-Augmented Generation...",
      "score": 0.95,
      "metadata": {"page": 1, "source": "my-document"}
    }
  ],
  "total_results": 4
}
```

### Ask a Question

```
POST /api/v1/documents/{document_id}/ask
```

Request body (`QuestionRequest`):

```json
{
  "question": "What is the main topic?",
  "strategy": "standard",
  "k_results": 4,
  "metadata_filter": {}
}
```

`strategy` accepts `"standard"` (RAG) or `"rerank"` (retrieval + Cohere reranking). `rerank` requires a `COHERE_API_KEY`.

Response (`QuestionAnswerResponse`):

```json
{
  "question": "What is the main topic?",
  "answer": "The main topic is...",
  "document_id": "uuid",
  "strategy": "standard",
  "source_documents": [
    {
      "page_content": "Relevant chunk text...",
      "metadata": {"page": 2, "source": "my-document"},
      "score": 0.92
    }
  ]
}
```

## Project Structure

```
backend/
├── app/
│   ├── api/                # Route handlers
│   │   └── routers/
│   ├── core/               # Config, dependencies, utilities
│   ├── infrastructure/     # LLM, embeddings, vector DB, database clients
│   │   ├── database/
│   │   ├── embeddings/
│   │   ├── llm/
│   │   └── vector_db/
│   ├── models/             # Pydantic request/response models
│   │   ├── requests/
│   │   └── responses/
│   ├── services/           # Business logic
│   │   ├── document/       # Text splitting
│   │   ├── ingest/         # PDF ingestion pipeline
│   │   ├── persistence/    # Document/interaction persistence
│   │   └── rag/            # Q&A and reranking strategies
│   ├── migrations/         # Alembic database migrations
│   ├── prompts/            # LLM prompt templates
│   └── utils/
├── tests/
│   ├── unit/               # Unit tests
│   └── behave/             # Integration tests (BDD)
├── main.py                 # FastAPI entry point
├── pyproject.toml          # Dependencies
└── uv.lock                 # Locked dependencies
```

## Configuration

Configuration comes from process environment variables, with defaults in `app/core/config.py`
(no env file is loaded). Reference values: `../k8s/base/backend/configmap.yaml` and
`configmap-local.yaml`. Main variables:

```bash
# LLM Provider
LOCAL_LLM=true                              # true=Ollama, false=cloud
USE_VERTEX_AI=false                         # cloud: Vertex AI instead of OpenAI
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:8b
OLLAMA_EMBEDDINGS_MODEL=nomic-embed-text-v2-moe

# Vector Database
VECTOR_DB_TYPE=chroma                       # chroma or pgvector
CHROMADB_HOST=localhost
CHROMADB_PORT=8000

# PGVector / app database
PGVECTOR_HOST=localhost
PGVECTOR_PORT=6024
PGVECTOR_USER=langchain
PGVECTOR_PASSWORD=langchain
PGVECTOR_DATABASE=langchain

# Secrets
USE_SECRETS=false                           # false: read keys from env vars (below)
OPENAI_API_KEY=...                          # cloud (non-Vertex) LLM and embeddings
COHERE_API_KEY=...                          # required for strategy=rerank
PROJECT_ID=...                              # only with USE_SECRETS=true outside GCP
```

Secrets are resolved by `get_secret()` in `app/core/helpers.py` (used by `openai_api_key` and
`cohere_api_key` in `Settings`). With `USE_SECRETS=false` (default) the keys come from
`OPENAI_API_KEY` / `COHERE_API_KEY`; a missing key resolves to an empty string. With
`USE_SECRETS=true` they are read from GCP Secret Manager (`openai-api-key`, `cohere-api-key`)
in the project returned by the GCP metadata server, or `PROJECT_ID` when not running on GCP;
if the lookup fails with a non-Google API error, it falls back to the env var. The `rerank`
strategy needs a real `COHERE_API_KEY`.

See `../docs/guides/setup.md` for full configuration reference.

## Testing

### Unit Tests

```bash
pytest tests/unit -v
```

### Integration Tests (BDD)

Requires running backend at `http://localhost:8106`:

```bash
BACKEND_URL=http://localhost:8106 behave tests/behave -v
```

### Linting and Type Checking

```bash
ruff check app
ruff format app
mypy app
```

See `../docs/development/testing.md` for detailed testing guide.

## Database Migrations

```bash
# Check current version
alembic current

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Create new migration from model changes
alembic revision --autogenerate -m "description"
```

Migrations are auto-generated from SQLAlchemy models. Always review before applying.

## Key Services

- **DocumentIngestionService**: PDF extraction, chunking, embedding, storage
- **QAService**: Standard RAG (retrieve → LLM)
- **RerankService**: Retrieve → rerank → LLM
- **DocumentService**: Document registry and deduplication
- **InteractionService**: Interaction logging for analytics

See `../docs/reference/architecture.md` for detailed service descriptions.

## Vector Database

### ChromaDB

Default, simpler setup. Initialize once:

```bash
python admin_chroma.py
```

### PGVector

Requires PostgreSQL with pgvector extension. Run migrations:

```bash
alembic upgrade head
```

Switch between backends via `VECTOR_DB_TYPE` environment variable.
