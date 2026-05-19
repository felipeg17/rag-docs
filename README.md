# rag-docs

A modular, experimental FastAPI backend for Retrieval-Augmented Generation with PDF document processing. rag-docs ingests PDF documents, extracts and chunks text, generates embeddings, and provides APIs for semantic search and question-answering with support for multiple LLM providers and retrieval strategies.

## Overview

rag-docs is designed for researchers and backend developers exploring RAG systems. It provides flexibility in vector databases (ChromaDB or PGVector), LLM providers (Ollama, OpenAI, Vertex AI), and retrieval strategies (standard RAG or reranking with Cohere).

**Key features:**

- PDF ingestion with text extraction and chunking
- Vector database abstraction (ChromaDB, PGVector)
- Multiple LLM providers (Ollama, OpenAI, Vertex AI)
- Retrieval strategies: standard RAG and reranking
- PostgreSQL persistence for documents and interactions
- Streamlit-based frontend UI
- Docker Compose and Kubernetes deployment options

## Getting Started

### Kubernetes with Skaffold (Recommended)

Requires Minikube and Skaffold:

```bash
# Start Minikube
minikube start --driver=docker --memory=4096 --cpus=3

# Create API secrets (or use dummy values for Ollama)
kubectl create secret generic api-keys \
  --from-literal=OPENAI_API_KEY=dummy \
  --from-literal=COHERE_API_KEY=dummy

# Deploy with Skaffold
skaffold dev --profile local,ollama -f k8s/skaffold.yaml
```

Access the services:

- **Backend API**: http://localhost:8106
- **Frontend**: http://localhost:8501
- **API Docs**: http://localhost:8106/docs (Swagger UI)

## API Endpoints

The backend provides REST APIs for document ingestion, search, and question-answering:

| Endpoint                                 | Method | Description                           |
| ---------------------------------------- | ------ | ------------------------------------- |
| `/health`                                | GET    | Health check                          |
| `/api/v1/documents`                      | POST   | Ingest PDF document                   |
| `/api/v1/documents/{document_id}/search` | POST   | Semantic search                       |
| `/api/v1/documents/{document_id}/ask`    | POST   | Question answering (RAG or reranking) |

Interactive API documentation available at `/docs` (Swagger UI) or `/redoc` (ReDoc).

## Architecture

rag-docs uses FastAPI dependency injection to wire LLM clients, vector databases, and services. Documents are split into chunks, embedded, and stored in a vector database. On retrieval, relevant chunks are fetched and passed to an LLM for answer generation.

## Configuration

Key environment variables:

| Variable         | Values              | Description                            |
| ---------------- | ------------------- | -------------------------------------- |
| `LOCAL_LLM`      | `true`/`false`      | Use Ollama (true) or cloud LLM (false) |
| `USE_VERTEX_AI`  | `true`/`false`      | Use Vertex AI when `LOCAL_LLM=false`   |
| `VECTOR_DB_TYPE` | `chroma`/`pgvector` | Vector database backend                |
| `USE_SECRETS`    | `true`/`false`      | Load API keys from GCP Secret Manager  |

See [SETUP.md](docs/SETUP.md) for complete variable reference.

## Project Structure

```
rag-docs/
├── backend/              # FastAPI application
│   ├── app/              # Source code (core, services, APIs)
│   ├── tests/            # Unit and integration tests
│   ├── main.py           # Entry point
│   └── pyproject.toml
├── frontend/             # Streamlit UI
├── k8s/                  # Kubernetes manifests and Skaffold
├── docs/                 # Technical documentation
└── CLAUDE.md             # Developer guide
```

## Documentation

- [CLAUDE.md](CLAUDE.md) — Comprehensive project guide (for Claude Code)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — System design and component details
- [docs/SETUP.md](docs/SETUP.md) — Detailed setup and configuration
- [docs/TESTING.md](docs/TESTING.md) — Testing strategies and examples
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) — How to contribute
- [backend/README.md](backend/README.md) — Backend-specific guide
- [frontend/README.md](frontend/README.md) — Frontend-specific guide
- [k8s/README.md](k8s/README.md) — Kubernetes deployment

## Status

This is an experimental research tool. Features and APIs may change. We actively maintain and welcome feedback.
