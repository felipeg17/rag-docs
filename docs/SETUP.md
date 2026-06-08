# Setup and Configuration

## Prerequisites

- Python >=3.10.12,<3.11
- Docker and Docker Compose (for containerized setup)
- `uv` package manager (for local development)
- PostgreSQL 13+ (for PGVector backend, or pgvector service in Docker)

## Environment Setup

Each component has its own `.env.template` file (e.g., `backend/backend.env.template`, `frontend/frontend.env.template`) listing the most important environment variables.

### Backend Configuration

### LLM Provider Selection

Choose one of three setups:

**Option A: Ollama (Local, Recommended for Development)**

```bash
LOCAL_LLM=true
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen3:8b
OLLAMA_EMBEDDINGS_MODEL=nomic-embed-text-v2-moe
```

**Option B: OpenAI**

```bash
LOCAL_LLM=false
USE_VERTEX_AI=false
OPENAI_API_KEY=sk-...
```

**Option C: Vertex AI**

```bash
LOCAL_LLM=false
USE_VERTEX_AI=true
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### Vector Database Selection

```bash
# ChromaDB (default)
VECTOR_DB_TYPE=chroma
CHROMADB_HOST=chromadb
CHROMADB_PORT=8000

# Or PGVector
VECTOR_DB_TYPE=pgvector
PGVECTOR_HOST=localhost
PGVECTOR_PORT=6024
PGVECTOR_USER=langchain
PGVECTOR_PASSWORD=langchain
PGVECTOR_DATABASE=langchain
```

### Secrets Management

```bash
# Option 1: Environment variables (default)
USE_SECRETS=false
OPENAI_API_KEY=sk-...
COHERE_API_KEY=...

# Option 2: GCP Secret Manager
USE_SECRETS=true
PROJECT_ID=your-gcp-project-id
```

When `USE_SECRETS=false`, the app reads `OPENAI_API_KEY` and `COHERE_API_KEY` from environment variables. When `true`, it fetches them from GCP Secret Manager using `PROJECT_ID` to locate the project.

### Frontend Configuration (frontend.env)

```bash
API_HOST=localhost
API_PORT=8106
```

## Local Development

### 1. Install Backend Dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### 2. Initialize Databases

If using ChromaDB, initialize the tenant and database:

```bash
cd backend
python admin_chroma.py
```

If using PGVector, run migrations:

```bash
cd backend
alembic upgrade head
```

### 3. Start Backend

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8106
```

### 4. Start Frontend (separate terminal)

```bash
cd frontend
python -m venv .venv
source .venv/bin/activate
uv pip install -e .
streamlit run front.py
```

Frontend runs at http://localhost:8501.

## Database Migrations (Alembic)

Run from `backend/`:

```bash
# Check current migration
alembic current

# Apply all pending migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1

# Create a migration from model changes
alembic revision --autogenerate -m "Add new column"
```

Migrations are in `backend/app/migrations/versions/`. Always review auto-generated migrations before applying.

## Testing

### Unit Tests

```bash
cd backend
pytest tests/unit -v
```

### Integration Tests (BDD)

Requires running backend at `http://localhost:8106`:

```bash
cd backend
BACKEND_URL=http://localhost:8106 behave tests/behave -v
```

Integration tests run only on `main` branch or with `integration-tests` label in CI.

## Kubernetes Deployment

See [k8s/README.md](../k8s/README.md) for Kubernetes setup with Skaffold or kubectl.