# Backend

FastAPI-based server for document ingestion and RAG-powered question answering.

## Overview

The backend provides REST APIs for:
- **Document ingestion**: Upload PDFs, extract text, chunk, and embed
- **Search**: Semantic similarity search on document chunks
- **Question answering**: Retrieve relevant chunks and generate answers via LLM
- **Reranking**: Retrieve → rerank with Cohere → answer (alternative strategy)

## Quick Start

### Docker

```bash
cp image.env.template image.env
# Edit image.env and set BACKEND_IMAGE_NAME and IMAGE_TAG
docker compose --env-file image.env --profile backend up --build
```

Backend runs at `http://localhost:8106`.

### Local Development

```bash
python -m venv .venv
source .venv/bin/activate
uv pip install -e .
cp backend.env.template backend.env

# Edit backend.env with your configuration

# Initialize databases (if using ChromaDB)
python admin_chroma.py

# Or run migrations (if using PGVector)
alembic upgrade head

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8106
```

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

Copy `backend.env.template` to `backend.env` and configure:

```bash
# LLM Provider
LOCAL_LLM=true                              # true=Ollama, false=cloud
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen3:8b
OLLAMA_EMBEDDINGS_MODEL=nomic-embed-text-v2-moe

# Vector Database
VECTOR_DB_TYPE=chroma                       # chroma or pgvector
CHROMA_HOST=chroma
CHROMA_PORT=8000

# Database
DATABASE_URL=postgresql://user:pass@localhost/ragdocs

# Secrets
USE_SECRETS=false
```

See `../docs/SETUP.md` for full configuration reference.

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

See `../docs/TESTING.md` for detailed testing guide.

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

See `../docs/ARCHITECTURE.md` for detailed service descriptions.

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
