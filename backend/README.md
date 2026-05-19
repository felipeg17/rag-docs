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
cd ..
docker compose --profile backend up --build
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

### Health Check

```bash
GET /health
```

### Ingest Document

```bash
POST /api/v1/documents
Content-Type: application/json

{
  "titulo": "my-document",
  "contenido": "base64-encoded-pdf-content"
}
```

Response:
```json
{
  "document_id": "doc-uuid",
  "titulo": "my-document",
  "chunks_created": 42,
  "content_hash": "sha256-hash"
}
```

### Search Documents

```bash
POST /api/v1/documents/{document_id}/search
Content-Type: application/json

{
  "query": "what is RAG?",
  "k": 5
}
```

Response:
```json
{
  "query": "what is RAG?",
  "results": [
    {"chunk": "text...", "score": 0.95},
    {"chunk": "text...", "score": 0.88}
  ]
}
```

### Ask Question

```bash
POST /api/v1/documents/{document_id}/ask
Content-Type: application/json

{
  "pregunta": "what is the main topic?",
  "estrategia": "standard"
}
```

Strategies: `standard` (RAG) or `rerank` (Cohere reranking).

Response:
```json
{
  "respuesta": "The main topic is...",
  "documentos_fuente": [
    {"chunk": "text...", "score": 0.92}
  ]
}
```

## Project Structure

```
backend/
├── app/
│   ├── core/               # Config, dependencies, utilities
│   ├── infrastructure/     # LLM, embeddings, database clients
│   ├── models/             # SQLAlchemy models
│   ├── repositories/       # Data access layer
│   ├── routes/             # API route handlers
│   ├── schemas/            # Pydantic request/response models
│   ├── services/           # Business logic
│   │   ├── ingest/         # Document ingestion
│   │   ├── rag/            # Q&A and retrieval strategies
│   │   ├── document/       # Text splitting
│   │   └── persistence/    # Document/interaction persistence
│   └── migrations/         # Alembic database migrations
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

## LLM Providers

### Ollama (Local, Recommended for Development)

```bash
LOCAL_LLM=true
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen3:8b
```

### OpenAI

```bash
LOCAL_LLM=false
USE_VERTEX_AI=false
OPENAI_API_KEY=sk-...
```

### Vertex AI (Google Cloud)

```bash
LOCAL_LLM=false
USE_VERTEX_AI=true
GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

## Troubleshooting

### Port 8106 Already in Use

Change port in Docker Compose or uvicorn command:

```bash
uvicorn main:app --reload --port 8107
```

### Database Connection Error

Verify `DATABASE_URL` and PostgreSQL is running:

```bash
docker compose logs postgres
```

### ChromaDB Not Found

Initialize ChromaDB:

```bash
python admin_chroma.py
```

### Import Errors

Ensure you're in the correct directory and virtual environment is activated:

```bash
cd backend
source .venv/bin/activate
```

## Contributing

See `../docs/CONTRIBUTING.md` for guidelines.

## Resources

- [Architecture](../docs/ARCHITECTURE.md)
- [Setup Guide](../docs/SETUP.md)
- [Testing Guide](../docs/TESTING.md)
- [Main README](../README.md)
