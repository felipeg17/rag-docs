# Setup and Configuration

This guide covers environment setup, configuration variables, and running rag-docs locally or in Docker.

## Prerequisites

- Python 3.10+
- Docker and Docker Compose (for containerized setup)
- `uv` package manager (for local development)
- PostgreSQL 13+ (for PGVector backend, or pgvector service in Docker)

## Environment Setup

### 1. Copy Template Configuration

```bash
cd backend
cp backend.env.template backend.env
cd ../frontend
cp frontend.env.template frontend.env
cd ..
```

### 2. Backend Configuration (backend.env)

#### LLM Provider Selection

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

#### Vector Database Selection

```bash
# ChromaDB (default, simpler setup)
VECTOR_DB_TYPE=chroma
CHROMA_HOST=chroma
CHROMA_PORT=8000

# Or PGVector (requires PostgreSQL)
VECTOR_DB_TYPE=pgvector
DATABASE_URL=postgresql://user:password@postgres:5432/ragdocs
```

#### Secrets Management

```bash
# Option 1: Environment variables
USE_SECRETS=false

# Option 2: GCP Secret Manager (requires GCP credentials)
USE_SECRETS=true
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
GCP_PROJECT_ID=your-project-id
```

#### Other Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/ragdocs
DB_ECHO=false  # Set to true for SQL logging

# Logging
LOG_LEVEL=INFO

# API
BACKEND_URL=http://localhost:8106
```

### 3. Frontend Configuration (frontend.env)

```bash
BACKEND_URL=http://localhost:8106
```

## Docker Compose Setup

### Start All Services

```bash
# From project root
docker compose --env-file image.env --profile full up --build
```

Services:
- `backend` (FastAPI) — http://localhost:8106
- `frontend` (Streamlit) — http://localhost:8501
- `postgres` (PostgreSQL)
- `chroma` (ChromaDB, if VECTOR_DB_TYPE=chroma)
- `ollama` (Ollama, if LOCAL_LLM=true)

### Start Backend Only

```bash
docker compose --profile backend up --build
```

### View Logs

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

### Stop Services

```bash
docker compose down
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

## Troubleshooting

### PostgreSQL Connection Refused

Ensure PostgreSQL is running:

```bash
# Docker Compose
docker compose ps postgres

# Local
brew services start postgresql  # macOS
```

### ChromaDB Not Initializing

Run admin script:

```bash
cd backend
python admin_chroma.py
```

### API Key Not Found

Check `backend.env` has correct variables. If using `USE_SECRETS=true`, verify GCP credentials.

### Vector Database Selection Not Working

Verify `VECTOR_DB_TYPE` is set to `chroma` or `pgvector` in `backend.env`.

## Next Steps

- See [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- See [TESTING.md](TESTING.md) for testing details
- See [backend/README.md](../backend/README.md) for backend-specific info
