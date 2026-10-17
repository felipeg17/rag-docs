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
  title VARCHAR(1000) NOT NULL,
  document_type VARCHAR(200) NOT NULL,
  content_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA-256
  file_size_bytes INT,
  page_count INT,
  status VARCHAR(50) DEFAULT 'active',
  created_at TIMESTAMP WITH TIME ZONE,
  updated_at TIMESTAMP WITH TIME ZONE
)

-- Search interactions
search_interactions (
  id UUID PRIMARY KEY,
  document_id UUID NOT NULL,
  query_text TEXT NOT NULL,
  k_results INT,
  results_count INT,
  avg_similarity_score FLOAT,  -- mean /search score (cosine similarity, 0-1); rows before SPEC-001 hold mean distances, not backfilled
  execution_time_ms INT,
  session_id UUID,
  user_id VARCHAR(255),
  created_at TIMESTAMP WITH TIME ZONE,
  updated_at TIMESTAMP WITH TIME ZONE
)

-- Q&A interactions
qa_interactions (
  id UUID PRIMARY KEY,
  document_id UUID NOT NULL,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  strategy VARCHAR(50),  -- 'standard' or 'rerank'
  k_results INT,
  llm_model VARCHAR(100),
  embedding_model VARCHAR(100),
  execution_time_ms INT,
  tokens_used INT,
  session_id UUID,
  user_id VARCHAR(255),
  feedback_text TEXT,
  created_at TIMESTAMP WITH TIME ZONE,
  updated_at TIMESTAMP WITH TIME ZONE
)
```

### Vector Database Storage

- ChromaDB: one collection (`chromadb_collection`, default `rag-docs`); each chunk carries `titulo` (document title) and `tipo_documento` metadata
- PGVector: `vector` schema, `rag_documents` table with `titulo` and `tipo_documento` metadata columns (managed by LangChain)
- Retrieval is scoped by `titulo` only (see [API Endpoints](#api-endpoints)). `tipo_documento` is written at ingestion but not read by retrieval.

Both backends measure similarity with cosine distance, set in code (not configurable):

- ChromaDB: the collection is created with `{"hnsw:space": "cosine"}` by `ChromaDBClient.get_or_create_collection`, `Chroma(collection_metadata=...)` and `admin_chroma.py`
- PGVector: `PGVectorStore.create_sync(distance_strategy=DistanceStrategy.COSINE_DISTANCE)`, the library default, passed explicitly

An existing ChromaDB collection with another space (`l2` is Chroma's default when none is given) is refused: `get_or_create_collection` raises `RuntimeError` naming the collection and its space. This happens when the vector repository is built, not at startup; the failed build is not cached, so every request that needs the repository (ingestion included) fails until the collection is recreated. The backend never deletes or modifies the collection. Chroma cannot change a collection's space, so drop the collection and re-ingest the PDFs (`POST /api/v1/documents` re-ingests a PDF whose title is missing from the vector store).

## API Endpoints

| Method | Endpoint                                 | Handler            |
| ------ | ---------------------------------------- | ------------------ |
| GET    | `/health`                                | Health check       |
| POST   | `/api/v1/documents`                      | Document ingestion |
| POST   | `/api/v1/documents/{document_id}/search` | Similarity search  |
| POST   | `/api/v1/documents/{document_id}/ask`    | Question answering |

`{document_id}` is the document title (not UUID), used for vector database filtering.

The web UI reaches these through its own origin: `/api/v1/*` unchanged and `/health` as
`/api/health` (see [Frontend](#frontend)).

### Retrieval scope

`/search` and `/ask` (both strategies) retrieve only chunks whose `titulo` equals `{document_id}`. The filter comes from `build_document_filter` in `app/infrastructure/vector_db/filters.py` and has one shape, valid on both backends:

- `metadata_filter` empty or absent: `{"titulo": {"$eq": <title>}}`
- Otherwise: `{"$and": [<title clause>, <one clause per metadata_filter key>]}`. The client filter is AND-ed with the title, so it can only narrow the scope. It is passed through without validation; some operators exist on one backend only.

`document_type` (ingestion request) is stored as `tipo_documento` chunk metadata and `documents.document_type`, but retrieval does not filter on it unless the client's `metadata_filter` names it.

### Search score

`/search` returns each result's `score` as a cosine similarity in [0, 1], higher is better: `1 − cosine distance`, clamped to [0, 1] (`cosine_distance_to_similarity` in `app/infrastructure/vector_db/scoring.py`, applied by each repository's own `similarity_search_with_relevance_scores` wrapper, not LangChain's method of the same name). Results are in non-increasing `score` order. `/ask` `source_documents` carry no score.

## Frontend

A single-page app in `frontend/src/` (Vite, React 19, TypeScript strict), built into static files
and served by nginx-unprivileged. It has two views, Upload and Ask, picked by the URL hash
(`#upload` by default, `#ask`; `frontend/src/app.tsx:12-14`). UI copy is Spanish. Uploaded titles
(offered as suggestions in Ask) and the per-title question threads live in memory only
(`app.tsx:22-25`); nothing is written to browser storage.

### Same-origin proxy

The browser talks only to the frontend's origin. The API client's base URL is `/api`
(`frontend/src/api/client.ts:43-46`), so the bundle holds no backend host. The backend adds no
CORS middleware (`backend/main.py`), so calling it cross-origin would not work anyway.

In the image, nginx runs as UID 101 and listens on 8502
(`frontend/nginx/default.conf.template`, `frontend/Dockerfile`):

| Browser path | nginx | Template lines |
| --- | --- | --- |
| `/api/v1/*` | Proxied to `http://${API_HOST}:${API_PORT}`. `proxy_pass` has no URI, so the path goes upstream as the browser sent it, percent-encoding included. | 17-26 |
| `/api/health` (exact) | Proxied to the backend's `/health` | 28-34 |
| Any other `/api/*` | `404`, not proxied | 36-39 |
| `/assets/*` | Hashed build output, cached `immutable`; `404` if missing | 41-45 |
| Anything else | The file if it exists, else `index.html` (cached `no-cache`) | 47-51 |

- **Upstream.** The image's envsubst step renders the template when the container starts,
  substituting only `API_*` variables (`NGINX_ENVSUBST_FILTER=^API_` in the Dockerfile). nginx
  resolves the host when it loads the configuration. An unresolvable `API_HOST` stops nginx with
  `[emerg] host not found in upstream` (executed against the image on 2026-10-16). That nginx
  does not re-resolve the name afterwards is inferred from the `ngx_http_proxy_module` docs and
  was not tested. Values:
  `k8s/base/frontend/configmap.yaml` (`rag-docs-backend`, `8106`; a change needs a pod restart).
  The frontend has no env file. The Vite dev proxy targets `API_PROXY_TARGET`, default
  `http://localhost:8106` (`frontend/vite.config.ts:5`).
- **Limits.** `client_max_body_size 30m` covers the largest ingest body, a 20 MiB PDF in base64
  (⌈20 MiB × 4/3⌉ = 27,962,027 bytes) plus the JSON around it. `proxy_read_timeout` and
  `proxy_send_timeout` are `300s`, at least the client's longest timeout. The client's limits are
  `MAX_PDF_BYTES` (20 MiB) and timeouts of 5 s (health), 300 s (ingest) and 180 s (ask)
  (`client.ts:10-17`).
- **Headers.** `frontend/nginx/security-headers.conf` sets `X-Content-Type-Options: nosniff`,
  `Referrer-Policy: no-referrer`, `X-Frame-Options: DENY` and a same-origin
  `Content-Security-Policy`. It is included per location, because nginx does not inherit
  `add_header` into a location that sets its own.
- **Errors.** The client turns non-2xx, timeout and network failures into an `ApiError` of kind
  `http`, `timeout` or `network`, and logs 5xx `detail` with `console.error` (`client.ts:60-76`).
  `errorMessage` maps each error to fixed Spanish copy (`frontend/src/api/errors.ts:23-50`). The
  backend's `detail` is never shown.

In development, `npm run dev` serves the app with a Vite proxy (`frontend/vite.config.ts`) that has
the same two API routes, to `API_PROXY_TARGET` (default `http://localhost:8106`). The variable is
not `VITE_`-prefixed, so it never reaches the bundle. The dev proxy has no `/api/*` 404 route.

### Titles in the URL path

`{document_id}` is the title, and the client encodes it with `encodeURIComponent`
(`client.ts:110`). That covers spaces, `?`, `#` and `%`. Two kinds of title still cannot reach
`/search` or `/ask`:

- **Titles containing `/`.** uvicorn decodes the path before routing, so `%2F` becomes `/`, and
  Starlette matches `{document_id}` with `[^/]+`.
- **`.` and `..`.** `encodeURIComponent` leaves dots alone, and the browser's URL parser removes
  dot segments: `/api/v1/documents/../ask` becomes `/api/v1/ask`.

The UI rejects these titles before uploading or asking (`validateTitle`,
`frontend/src/validation.ts:15-27`), along with empty titles and titles over 1000 characters
(`documents.title VARCHAR(1000)`). The backend does not reject them: `DocumentIngestRequest.title`
has no such constraint (`app/models/requests/document_request.py:8`), so such a title ingested
through the API directly is stored but cannot be searched or asked. Library versions and source
lines are in [SPEC-002](../specs/SPEC-002-web-frontend.md) § Context.

### API types

The frontend's request and response types are generated, never hand-written:

1. `backend/export_openapi.py` writes the FastAPI app's schema to `backend/openapi.json` offline
   (no server, database or LLM). `backend/tests/unit/openapi_snapshot_test.py` fails when the
   committed file differs from what the app produces.
2. `npm run gen:api` (in `frontend/`) generates `frontend/src/api/openapi_gen.ts` from it with
   `openapi-typescript`. `npm run check:api` fails when that file is stale; CI runs it on changes
   to `frontend/**` or `backend/openapi.json`.
3. `frontend/src/api/types.ts` only aliases the generated schemas.

The regeneration workflow is in `frontend/README.md` § Types (contract).

## Configuration Management

Configuration sources, in order of precedence:

1. GCP Secret Manager (if `USE_SECRETS=true`) — used for API keys (`openai-api-key`, `cohere-api-key`)
2. Process environment variables. No env file is read: `Settings.model_config` sets no `env_file`
   (`app/core/config.py:92-96`). In Kubernetes they come from the `backend-config` configmap and the
   `api-keys` secret through `envFrom` (`k8s/base/backend/deployment.yaml:27-31`).
3. Hardcoded defaults in `app/core/config.py`

The `USE_SECRETS` env var controls whether `get_secret()` in `app/core/helpers.py` fetches from GCP Secret Manager or falls back to environment variables.
