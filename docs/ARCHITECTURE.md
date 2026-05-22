# Architecture

`rag-docs` is built on `FastAPI` with a service-oriented architecture.

## High-Level Flow

```
PDF Upload
    ↓
Base64 Decode & Text Extraction (PyMuPDF)
    ↓
Text Splitting (Recursive or Semantic)
    ↓
Embedding Generation (Ollama or cloud provider)
    ↓
Vector Database Storage (ChromaDB or PGVector)
    ↓
Document Registry (PostgreSQL)

Search/Ask Request
    ↓
Vector Similarity Retrieval
    ↓
[Optional] Reranking (Cohere)
    ↓
LLM Answer Generation
    ↓
Response + Source Documents
```

## Dependency Injection

FastAPI _DI_ in `app/core/dependencies.py` wires the entire application:

```
HTTP Request
    ↓
Singletons (cached):  get_llm_client, get_embeddings_client,
                      get_vector_db_repository, get_db_client
    ↓
Request-scoped:       get_db_session → get_document_repository → get_document_service
                      get_db_session → get_*_interaction_repository → get_interaction_service
    ↓
Endpoint Handler
```

## Core Services

### DocumentIngestionService

- Location: `app/services/ingest/ingestion.py`
- Handles PDF upload, text extraction, chunking, and vector storage
- Returns document metadata and chunk count
- Supports two chunking strategies:
  - **Recursive**: Fast, configurable chunk size/overlap
  - **Semantic**: Embedding-aware boundaries (slower, more accurate splits)

### QAService

- Location: `app/services/rag/qa_service.py`
- Retrieves relevant document chunks
- Sends chunks + user question to LLM
- Returns answer with source documents
- Standard RAG strategy

### RerankService

- Location: `app/services/rag/rerank_service.py`
- Retrieves candidate chunks (retrieval)
- Uses Cohere to rerank top results
- Sends top reranked chunks to LLM

### DocumentService

- Location: `app/services/persistence/document_service.py`
- Manages document registry in PostgreSQL
- Tracks documents by SHA-256 content hash (prevents duplicates)
- Stores document metadata (title, upload date, etc.)

### InteractionService

- Location: `app/services/persistence/interaction_service.py`
- Logs every search and Q&A interaction to PostgreSQL
- Tracks user queries, retrieved documents, answers
- Enables analytics and debugging

## Vector Database

### ChromaDB

- HTTP client connecting to ChromaDB server
- Tenant/database/collection isolation
- Requires: `admin_chroma.py` to initialize tenant/database on first run

### PGVector

- PostgreSQL with pgvector extension
- Two schemas:
  - `app`: Application tables (documents, interactions) — managed by Alembic
  - `vector`: Embeddings — managed by LangChain

Switch between backends via `VECTOR_DB_TYPE` environment variable.

## LLM Providers

### Ollama (Local)

- Default: `qwen3:8b`
- Embeddings: `nomic-embed-text-v2-moe`
- Runs locally
- Set `LOCAL_LLM=true`

### OpenAI

- Model: `gpt-4.1-nano`
- Requires `OPENAI_API_KEY`
- Set `LOCAL_LLM=false`, `USE_VERTEX_AI=false`

### Vertex AI (Google Cloud)

- Model: `gemini-2.5-flash`
- Requires GCP credentials
- Set `LOCAL_LLM=false`, `USE_VERTEX_AI=true`

Configuration in `app/infrastructure/llm/client.py` and `app/infrastructure/embeddings/client.py`.

## Text Splitting

Configured in `app/services/document/text_splitter.py`:

- **Recursive**: `RecursiveCharacterTextSplitter` — splits by punctuation/whitespace, recursive fallback
- **Semantic**: `SemanticChunker` — uses embeddings to find natural boundaries

## Database Schema

### PostgreSQL (`app` schema)

```sql
-- Document registry
documents (
  id UUID PRIMARY KEY,
  titulo TEXT,
  content_hash VARCHAR(64),  -- SHA-256
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)

-- Search interactions
search_interactions (
  id UUID PRIMARY KEY,
  document_id UUID REFERENCES documents,
  query TEXT,
  retrieved_count INT,
  created_at TIMESTAMP
)

-- Q&A interactions
qa_interactions (
  id UUID PRIMARY KEY,
  document_id UUID REFERENCES documents,
  pregunta TEXT,
  respuesta TEXT,
  estrategia VARCHAR(20),  -- 'standard' or 'rerank'
  source_docs JSONB,
  created_at TIMESTAMP
)
```

### Vector Database Storage

- ChromaDB collections: Organized by document title as metadata filter
- PGVector: `vector` schema with embeddings and metadata (managed by LangChain)

## API Endpoints

| Method | Endpoint                                 | Handler            |
| ------ | ---------------------------------------- | ------------------ |
| GET    | `/health`                                | Health check       |
| POST   | `/api/v1/documents`                      | Document ingestion |
| POST   | `/api/v1/documents/{document_id}/search` | Similarity search  |
| POST   | `/api/v1/documents/{document_id}/ask`    | Question answering |

`{document_id}` is the document title (not UUID), used for vector database filtering.

## Configuration Management

Configuration sources (in order of precedence):

1. Environment variables (`.env` file or system)
2. GCP Secret Manager (if `USE_SECRETS=true`)
