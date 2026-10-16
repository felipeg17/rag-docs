# SPEC-001: Scope retrieval to the requested document and return true similarity scores

| Field | Value |
|---|---|
| Status | Done |
| Findings | F-001, F-031 |
| Issue | — |
| Domains | backend, qa, docs |
| Branch | `spec/SPEC-001-scope-retrieval-to-document` |
| Base | `dev` @ `200c4cf` |

## Context

`/search` and `/ask` take a document in the path (`{document_id}`, which is really the document
title: `backend/app/api/routers/v1/document.py:119,192`). They check that the title exists
(`document.py:127,202`), but retrieval never filters on it. As soon as more than one PDF is
ingested, results and answers can come from any document ([F-001](../findings/F-001-retrieval-not-scoped-to-document.md)).

Verified on `dev` @ `200c4cf` (2026-10-15):

- **`/ask`, standard**: `QAService.answer_question` builds the retriever with
  `filter={"tipo_documento": {"$eq": document_type}}` only (`backend/app/services/rag/qa_service.py:55-62`).
  The router passes the hardcoded `"documento-pdf"` (`document.py:220-224`) and never passes the title.
- **`/ask`, rerank**: `RerankService.answer_question` builds the same type-only filter (`backend/app/services/rag/rerank_service.py:65-72`),
  called from `document.py:211-215`.
- **`/ask`, `metadata_filter`**: `QuestionRequest.metadata_filter` (`backend/app/models/requests/search_request.py:18`)
  is accepted but never read by `ask_question` (`document.py:191-257`).
- **`/search`**: the router passes `request.metadata_filter` (`document.py:134-138`), which defaults to `{}`
  (`search_request.py:9`). Both repositories do `filter = metadata_filter or {"tipo_documento": "documento-pdf"}`
  (`backend/app/infrastructure/vector_db/repository.py:54`, `pgvector_repository.py:68`).
  - With `{}`, the type-only default applies.
  - With a non-empty filter, the client filter *replaces* the type filter.
  - Either way, no title clause is ever applied.
- **Chunk metadata**: every chunk carries `titulo`, `tipo_documento` and `pagina` (`backend/app/services/document/text_extractor.py:42-46`).
  On PGVector they are real columns (`backend/app/infrastructure/vector_db/pgvector_client.py:13-18`).
  So a title filter needs no re-ingestion.
- **`document_type` at ingestion**: `POST /api/v1/documents` stores the caller's `document_type`
  (`DocumentIngestRequest.document_type`, default `"documento-pdf"`: `backend/app/models/requests/document_request.py:9-10`)
  in Postgres and in chunk metadata (`document.py:51,66`). Retrieval always filters on `"documento-pdf"`
  (`document.py:213,222`; `repository.py:54`). So a document ingested with any other type is never
  retrieved by `/ask` or `/search`. When it is the only document, they return nothing. When other
  documents exist, they return *those* documents' chunks. The second case was executed in the
  backend venv: an in-memory Chroma held `doc-a` (`tipo_documento="custom-type"`) and `doc-b`
  (`"documento-pdf"`). `QAService.answer_question("alpha", "documento-pdf")` (with `FakeListLLM`)
  returned only `doc-b`'s chunk as a source.

### Library behavior (verified against installed sources pinned in `backend/uv.lock`)

| Library | Version | Fact | Where checked |
|---|---|---|---|
| `langchain-core` | 0.3.68 | `VectorStoreRetriever._get_relevant_documents` calls `vectorstore.similarity_search(query, **search_kwargs)`, so `search_kwargs["filter"]` reaches the store | `langchain_core/vectorstores/base.py:1074-1079` |
| `langchain-core` | 0.3.68 | `DeterministicFakeEmbedding` and `FakeListLLM` run offline. With an in-memory Chroma they drive `RetrievalQA` end to end with no network. | executed (probe below) |
| `langchain-chroma` | 0.2.4 | `filter` is passed to Chroma as `where=`, `where_document` as `where_document=` | `langchain_chroma/vectorstores.py:585-606,686-700` |
| `chromadb` | 1.0.12 | `validate_where` requires exactly one top-level key. It rejects multi-key dicts (`{"a":1,"b":2}`), `{}`, and `$and`/`$or` with fewer than 2 elements. Nested `$and`/`$or` is accepted. Logical operators are `$and`/`$or` only (`$not` is rejected). Field operators are `$eq $ne $gt $gte $lt $lte $in $nin` only (`$like`, `$exists` are rejected). | `chromadb/api/types.py:731-763` + executed |
| `chromadb` | 1.0.12 | `chromadb.EphemeralClient()` runs in-process. Through `langchain_chroma.Chroma`, `{"titulo": {"$eq": "doc-a"}}` returns `doc-a`'s chunk, whatever its `tipo_documento`, from both `similarity_search_with_score` and `as_retriever(...).invoke`. | executed |
| `langchain-postgres` | 0.0.16 | `PGVectorStore` (v2) accepts `$and`/`$or`/`$not`, multi-key dicts (implicit AND) and single-element `$and`. A field name is emitted raw as a SQL column, so it must be a valid identifier (`tipo-documento` raises `ValueError`, executed). A non-column key yields a SQL error (inferred from the SQL it emits; not executed, no database). An empty or absent filter means no `WHERE`. | `langchain_postgres/v2/async_vectorstore.py:606-618,1041-1240` + executed |
| `langchain-postgres` | 0.0.16 | `where_document` is not referenced anywhere in the package. It falls into `**kwargs` and is silently ignored. | `grep -rn where_document langchain_postgres/` → no match |

"Executed" means the filter shapes were run through `chromadb.api.types.validate_where` and
`AsyncPGVectorStore._create_filter_clause` in the backend venv. The in-memory Chroma probes ran
with `uv run --offline` in `backend/`. One filter shape is valid on both backends:

```python
{"titulo": {"$eq": "<title>"}}                                   # title only: one top-level condition
{"$and": [{"titulo": {"$eq": "<title>"}}, <client clause>, ...]}  # title + client filter: 2+ clauses
```

### Search score is a distance ([F-031](../findings/F-031-search-score-is-unbounded-distance.md))

Folded in on 2026-10-15 because it blocks AC-9. The T-2 live run (minikube, `local,chroma`,
Ollama `nomic-embed-text-v2-moe`) got a 500 from `/search`: score 1.708 > `le=1.0`.

Verified in the SPEC-001 working tree (T-1 applied, uncommitted) on 2026-10-15:

- `SearchResultItem.score` is `Field(..., ge=0.0, le=1.0, description="Similarity score")`
  (`backend/app/models/responses/search_response.py:8`). `responses_test.py:136-152` pins both bounds.
- `/search` copies the store score unchanged.
  - The call is `vdb_repo.similarity_search_with_score` (`document.py:135-139`).
  - The copy is `SearchResultItem(..., score=float(score), ...)` (`document.py:143-150`).
  - The same tuples go to `interaction_service.log_search` (`document.py:156-162`).
  - `InteractionService._calculate_avg_score` averages them into `avg_similarity_score`
    (`backend/app/services/persistence/interaction_service.py:35,83-88`).
  - A `ValidationError` becomes a 500 (`document.py:173-179`).
- Both repositories return the store's raw distance (`repository.py:59-64`, `pgvector_repository.py:72-77`).
- Neither backend configures a metric:
  - Chroma: `ChromaDBClient.get_or_create_collection` calls `create_collection(name=name)`
    (`backend/app/infrastructure/vector_db/chroma_client.py:36`), and `Chroma(...)` gets no
    `collection_metadata` (`repository.py:27-31`).
  - PGVector: `PGVectorStore.create_sync(...)` gets no `distance_strategy` (`pgvector_repository.py:41-47`).
  - No `hnsw:space` or `distance_strategy` appears anywhere in `backend/app`, `backend/tests` or `k8s/`.
- Other places that create the Chroma collection:
  - The k8s Chroma entrypoint creates only the tenant `dev` and the database `rag-database`
    (`k8s/base/vectordb/chroma/entrypoint.sh:14-23`). The backend creates the collection.
  - `backend/admin_chroma.py:64` (manual setup script, `docs/guides/setup.md:97-101`) creates
    `rag-docs` with `create_collection(name=collection_name)`, also with no metric.
- The k8s Chroma pod has no volume (`k8s/base/vectordb/chroma/deployment.yaml:17-35`: no
  `volumes`/`volumeMounts`), so restarting it wipes every collection.
- The Settings default collection is `rag-docs` (`backend/app/core/config.py:62`), and no configmap
  overrides it.
- Construction of the vector repository:
  - `get_vector_db_repository` is `lru_cache`d and built on the first request that needs it
    (`backend/app/core/dependencies.py:65-76`). The lifespan only heartbeats the clients
    (`backend/app/core/lifespan.py:31-37`).
  - After Chroma is recreated, the backend must be restarted too, or it keeps its old collection handle.
- PGVector has no persisted metric:
  - `PGEngine.init_vectorstore_table` takes no distance argument (no `distance` in `langchain_postgres/v2/engine.py`).
  - The repository applies no vector index (no `apply_vector_index` in `backend/`). The only Alembic
    `hnsw_index` is a drop of a legacy test table (`dc37733dbbf5_...py:142-155`).

| Library | Version | Fact | Where checked |
|---|---|---|---|
| `chromadb` (client) | 1.0.12 | `create_collection(name)` with no metric creates a collection whose `configuration_json["hnsw"]["space"]` is `"l2"`. `metadata={"hnsw:space": "cosine"}` gives space `"cosine"` and keeps the key in `metadata`. `configuration={"hnsw": {"space": "cosine"}}` gives space `"cosine"` with `metadata=None`. | executed (`EphemeralClient`) |
| `chromadb` (client) | 1.0.12 | `get_or_create_collection(name, metadata={"hnsw:space": "cosine"})` on an existing `l2` collection returns it **unchanged as `l2`**, with no error and no warning. The metric of an existing collection cannot be changed this way. | executed |
| `chromadb` (client) | 1.0.12 | Legacy `hnsw:space` metadata maps to the `space` configuration (`chromadb/api/collection_configuration.py:281-301`). The HTTP client sends `metadata` and `configuration` as given (`chromadb/api/fastapi.py:247-266`). `GET /api/v2/tenants/{t}/databases/{d}/collections/{name}` returns `configuration_json` (`fastapi.py:279-284`, `chromadb/types.py:171`). | source |
| `langchain-chroma` | 0.2.4 | `similarity_search_with_score` returns the distance, "Lower score represents more similarity" (`vectorstores.py:689`). `Chroma(collection_metadata=...)` forwards it as `metadata=` to `get_or_create_collection` (`vectorstores.py:285,335,344-348`). `_select_relevance_score_fn` reads only `metadata["hnsw:space"]` and falls back to L2 (`1 - d/√2`) when it is absent (`vectorstores.py:756-792`). | source + executed |
| `langchain-chroma` + `chromadb` | 0.2.4 / 1.0.12 | With `DeterministicFakeEmbedding(size=16)`, 20 chunks and an off-topic query, a cosine collection returned distances 0.64–1.46 in ascending order, 9 of them > 1. The default (`l2`) collection returned 18.97–56.65 (fake embeddings are not normalized). | executed |
| `langchain-core` | 0.3.68 | `_cosine_relevance_score_fn(d) = 1.0 - d`, with no clamp (`vectorstores/base.py:422-424`). `similarity_search_with_relevance_scores` only `warnings.warn`s on values outside [0, 1] (`base.py:534-566`). | source |
| `chromadb/chroma` (server) | 1.0.0 | Read-only `GET` of the live collection on minikube (`local,chroma`, 2026-10-15) returned `"metadata": null`, `"dimension": 768` and `"configuration_json": {"_type": "CollectionConfigurationInternal", "hnsw_configuration": {..., "space": "l2", ...}}`. The server's shape is `configuration_json["hnsw_configuration"]["space"]`, not the bindings' `configuration_json["hnsw"]["space"]`. The collection had been created with no metric (`chroma_client.py:36` on `200c4cf`), and the no-metric probe in the next row shows such a collection is `l2`. So 1.708 was a squared L2 distance. The `configuration_json` value itself is not evidence of the space (next row). | executed: `kubectl exec deploy/chromadb -- curl -s http://localhost:8000/api/v2/tenants/dev/databases/rag-database/collections/rag-docs` |
| `chromadb/chroma` (server) + `chromadb` (client) | 1.0.0 / 1.0.12 | **`configuration_json` always reports `hnsw_configuration.space == "l2"`**, whatever the collection's real metric. Probe on scratch collections (deleted after), vectors a=[2,0], b=[0,3], query [1,0]: (1) `metadata={"hnsw:space": "cosine"}` → distances [0.0, 1.0] (cosine), `metadata` kept as `{"hnsw:space": "cosine"}`, `configuration_json` reports `l2`; (2) `configuration={"hnsw": {"space": "cosine"}}` → distances [0.0, 1.0] (cosine), `metadata` `None`, `configuration_json` reports `l2`; (3) no metric → distances [1.0, 10.0] (squared L2). On this server the only trustworthy record of the space is `metadata["hnsw:space"]`. A collection created through `configuration` only cannot be told apart from an `l2` one without querying it. | executed by qa-agent during `/spec verify` (2026-10-15), 1.0.12 HTTP client against the minikube server; recorded in *Verification* (AC-19) |
| `chromadb` (client, local) | 1.0.12 | With `EphemeralClient`, `configuration_json["hnsw"]["space"]` matches the real metric in every case probed (same vectors as above): no metric → `l2` ([1.0, 10.0]); metadata cosine → `cosine`; metadata `l2` → `l2`; configuration cosine → `cosine` with `metadata` `None`; metadata `l2` + configuration cosine → `cosine` ([0.0, 1.0]) with `metadata` still `{"hnsw:space": "l2"}`; metadata cosine + configuration `l2` → `cosine`. So locally `metadata["hnsw:space"]` can disagree with the real space only when both `metadata` and `configuration` were given at creation. | executed (`EphemeralClient`, 2026-10-15) |
| `chromadb` (client) | 1.0.12 | `Collection.modify(metadata=...)` with an `hnsw:space` key raises `ValueError("Changing the distance function of a collection once it is created is not supported currently.")` before any request is sent. Through this client, `metadata["hnsw:space"]` therefore cannot be changed after creation. | `chromadb/api/models/CollectionCommon.py:508-514` + executed |
| `langchain-postgres` | 0.0.16 | `DistanceStrategy.COSINE_DISTANCE` (`<=>`, `cosine_distance`) is the default (`v2/indexes.py:21-29`). `create_sync` accepts `distance_strategy` (`v2/vectorstores.py:110-122`). The query computes `cosine_distance(embedding, q) AS distance`, orders by `<=>` and returns `row["distance"]` (`v2/async_vectorstore.py:593-620,769-786`). `DistanceStrategy` is not re-exported from `langchain_postgres`; import it from `langchain_postgres.v2.indexes`. | source |

Not verified (assumed):
- The deployed server is `chromadb/chroma:1.0.0` (`k8s/base/vectordb/chroma/Dockerfile:1`). QA's
  probe (table above) verified that `metadata={"hnsw:space": "cosine"}` sent by the 1.0.12 client is
  honored at creation. That the server never changes an existing collection's space is assumed:
  the 1.0.12 client refuses to send such a change (`CollectionCommon.py:508-514`), but the server
  itself was not probed with one.
- Server versions other than 1.0.0 were not probed. Whether a later server reports
  `configuration_json` truthfully is not known; the guard (Design) does not depend on it.
- pgvector's cosine distance lies in [0, 2]. This is from the definition (1 − cosine similarity);
  it was not executed.
- Whether Ollama `nomic-embed-text-v2-moe` returns unit-normalized vectors is not known. If it does
  not, cosine and L2 rank chunks differently, so the metric change can also change which chunks
  `/ask` retrieves. AC-10 is re-run for this reason.

## Goals

- Every retrieval behind `/search` and `/ask` (both strategies) returns only chunks of the
  requested document, on both Chroma and PGVector.
- A client-supplied `metadata_filter` can only narrow results within the document, never widen
  them. It is honored on `/ask` as well as `/search`.
- A document is retrievable whatever `document_type` it was ingested with.
- `/search` `score` is what its schema says: a similarity in [0, 1], higher is better, on both
  backends. A valid request never fails because of the score's magnitude.
- The distance metric is set explicitly (cosine) on both backends, not left to library or server
  defaults.

## Non-goals

- Changing document identity (title → UUID or content hash), title uniqueness, or storing a
  `document_id` in chunk metadata ([F-002](../findings/F-002-inconsistent-document-identity.md), #20;
  [F-023](../findings/F-023-mislabelled-path-params.md)). This spec scopes by `titulo`, the same key
  the existing 404 check uses (`document.py:127,202`).
- Ingestion of `document_type`. It is still accepted by `POST /api/v1/documents` and still stored
  in Postgres (`documents.document_type`) and in chunk metadata (`tipo_documento`). Only retrieval
  stops filtering on it.
- The rest of [F-024](../findings/F-024-unwritten-logged-fields.md) (#15). This spec removes the
  `document_type` argument from both `answer_question` methods. The hardcoded `"documento-pdf"` at
  `document.py:213,222` and its `TODO issue #15` comments therefore go away. What remains of F-024:
  - `llm_model` is never passed to `log_qa`, and `page_count` is never passed to `create_document`.
  - The ingestion-service default `"documento_pdf"` (`backend/app/services/ingest/ingestion.py:23`)
    differs from the request default `"documento-pdf"` (`document_request.py:10`). Through HTTP it
    is never reached, because the router always passes `request.document_type or "documento-pdf"`
    (`document.py:66`). After this spec it has no effect on retrieval either way; only the
    stored value would differ.
  - The repositories still default to `{"tipo_documento": "documento-pdf"}` when called with
    `metadata_filter=None` (`repository.py:54`, `pgvector_repository.py:68`). After this spec no
    route calls them with `None`, so the default is unreachable from the API. It is kept to stay
    minimal: changing it to "no filter" would mean omitting the `filter` kwarg, because Chroma
    rejects `{}`.
  - No canonical `document_type` value or vocabulary.
- Validating client `metadata_filter` keys or operators (OQ-2 decision (a)). The filter is passed
  through as given. Unknown keys or single-backend operators can fail inside the store and surface
  as a 500 (`document.py:170-178,259-267`). Error mapping belongs to
  [F-007](../findings/F-007-error-handling-leaks-internals.md).
- Moving or removing `where_document` ([F-012](../findings/F-012-chroma-only-where-document.md)).
  Its current behavior is kept as is: applied on Chroma, ignored on PGVector.
- Rerank sources ([F-008](../findings/F-008-rerank-near-noop.md)) and rerank context formatting
  ([F-004](../findings/F-004-rerank-context-not-formatted.md)).
- `backend/tests/fixtures/generate_golden_responses.py`, which filters on `tipo-documento`
  (`:127,180,257,322`). That key does not exist and is not a valid PGVector identifier.
- Frontend changes. `frontend/components/chatbot.py:15-21` already sends the title in the path and
  `metadata_filter: {}`. `frontend/components/qa_pdf.py:15,23` keeps sending
  `document_type: "documento-pdf"` on ingestion, which this spec does not change. URL encoding is
  [F-028](../findings/F-028-frontend-requests.md).
- Score and metric limits (F-031 scope):
  - Making the metric configurable (no `Settings` field), and supporting L2 or inner product. Cosine
    is a code constant.
  - Migrating an existing non-cosine Chroma collection in place. Chroma cannot change a collection's
    space (Context). The backend refuses such a collection (REQ-9) and never deletes it. Recreating it
    and re-ingesting is an operator step.
  - Backfilling `search_interactions.avg_similarity_score` rows written before this spec. They hold
    mean distances under an unknown metric and cannot be converted reliably. They are left as is.
  - A `score` on `/ask` `source_documents` (`SourceDocument.score` stays `None`, `document.py:234`)
    and a score threshold.
  - Regenerating `backend/tests/fixtures/golden_responses/` or changing
    `generate_golden_responses.py`. It keeps calling `similarity_search_with_score`, which keeps
    returning raw distances.
  - Building the vector repository at startup ([F-014](../findings/F-014-startup-not-fail-fast.md)).
    The REQ-9 refusal surfaces on the first request that needs the repository.

## Requirements

- **REQ-1**: When `/api/v1/documents/{document_id}/search` is called, the system shall return only
  chunks whose `titulo` equals `{document_id}`.
- **REQ-2**: When `/api/v1/documents/{document_id}/ask` is called with `strategy` `standard` or
  `rerank`, the system shall retrieve only chunks whose `titulo` equals `{document_id}`. This
  includes the `source_documents` returned for `standard`.
- **REQ-3**: When a request carries a non-empty `metadata_filter`, the system shall apply it in
  conjunction (AND) with the document scope on both endpoints. It shall never replace or widen the
  scope. An empty or absent `metadata_filter` adds no condition.
- **REQ-4**: Retrieval behind `/search` and `/ask` shall not filter on `tipo_documento`, unless the
  client's `metadata_filter` names it (REQ-3). A document shall be retrievable whatever
  `document_type` it was ingested with.
- **REQ-5**: REQ-1 to REQ-4 shall hold for both vector backends (`VECTOR_DB_TYPE` Chroma and
  PGVector). The document-scope filter shall use one shape that is valid in both grammars.
  Client-supplied clauses are passed through as given, without validation.
- **REQ-6**: The `where_document` behavior of each backend shall not change.
- **REQ-7**: On both vector backends, `/search` shall return each result's `score` as a cosine similarity in [0, 1], where 1
  is most similar. It is computed as `1 − cosine distance`, clamped to [0, 1]. Results shall be in
  non-increasing `score` order. A valid `/search` request shall not fail because of a score's value.
- **REQ-8**: Both vector backends shall measure similarity with cosine distance, set explicitly:
  - Chroma: the collection is created with the cosine space.
  - PGVector: the store queries with the cosine distance strategy.
- **REQ-9**: When the configured Chroma collection already exists with a space other than cosine,
  the backend shall refuse to use it, with an error that names the collection, its space, and that
  it must be recreated. It shall not delete or modify the collection.
- **REQ-10**: `search_interactions.avg_similarity_score` shall be the mean of the similarity
  scores returned by that `/search` call (REQ-7).

## Contracts

| Contract | Before | After | Breaking? |
|---|---|---|---|
| API models (`backend/app/models/`) | `DocumentSearchRequest.metadata_filter` and `QuestionRequest.metadata_filter` are `dict`, default `{}`, "Optional metadata filters" (`search_request.py:9,18`). `/search`: replaces the type filter. `/ask`: ignored. `DocumentIngestRequest.document_type` (`document_request.py:9-10`) is stored, and retrieval filters on the fixed `"documento-pdf"`. | `metadata_filter`: schema unchanged; `Field` description updated to state it is AND-ed with the document scope. `/search` and `/ask`: AND-ed with the document scope. `document_type`: schema and ingestion unchanged; no longer used for retrieval scoping. | Behavioral only. In-repo callers send `metadata_filter: {}` (`frontend/components/chatbot.py:21`, `backend/tests/behave/steps/document_qa_steps.py:21`, `document_qa_rerank_steps.py:16`, `document_processing_steps.py:106`) and are unaffected. Documents ingested with a non-default `document_type` become retrievable; documents with the default are unaffected. |
| API models: `/search` score semantics (F-031) | `SearchResultItem.score` is declared `ge=0.0, le=1.0`, "Similarity score" (`search_response.py:8`). In practice it holds the raw store distance: lower is better, and above 1 it causes a 500. | Schema, field name, description and bounds are unchanged. The value is a cosine similarity in [0, 1], higher is better, in non-increasing order (REQ-7). | Behavioral. The value now matches the documented schema, but its ordering is the reverse of what clients observed before. Migration path: none needed. No in-repo consumer calls `/search` (`frontend/components/qa_pdf.py:19` and `chatbot.py:15` call only `POST /documents` and `/ask`), and the only behave scenario that calls it is T-2's, which needs this fix. No deprecation window. |
| HTTP routes / status codes | `/search` returns 500 when any hit's distance is > 1 (`document.py:143-150,173-179`). | `/search` returns 200 for those requests. No route changes. | No |
| `Settings` ↔ configmaps ↔ `backend.env.template` | — | None. The metric is a code constant (Non-goals). The Chroma entrypoint creates no collection (`entrypoint.sh:14-23`), so it needs no change. | No |
| DB schema / Alembic migration | — | No schema change and no migration. `documents.document_type` is still written. The meaning of `search_interactions.avg_similarity_score` changes from a mean store distance to a mean cosine similarity in [0, 1] (REQ-10). Existing rows are not backfilled (Non-goals). | Behavioral (column meaning). Rows written before and after the change are not comparable. |
| Vector DB metadata / collection / table | Retrieval keys as before. Chroma collection created with no metric: `l2` (1.0.12 client probe, and confirmed on the live 1.0.0 server). PGVector queries use the library default `COSINE_DISTANCE`. | Retrieval reads the existing `titulo` key (`text_extractor.py:43`, PG column `pgvector_client.py:14`). `tipo_documento` is still written at ingestion and no longer read by retrieval. The Chroma collection is created with `{"hnsw:space": "cosine"}`, through both `ChromaDBClient.get_or_create_collection` and `Chroma(collection_metadata=...)`. The backend refuses an existing non-cosine collection (REQ-9). PGVector passes `distance_strategy=DistanceStrategy.COSINE_DISTANCE` explicitly, the same value as the default. The PG table, columns and vector dimension are unchanged. | Chroma: yes. An existing collection must be dropped and its documents re-ingested. Path: under k8s, restart the `chromadb` pod (no volume), then restart `rag-docs-backend`, then re-upload the PDFs. `POST /api/v1/documents` re-ingests a PDF when it is missing from the vector store (`document.py:57-69`). Agreed by the user for local data. PGVector: no; no re-ingestion. Changing the metric can change `/ask` retrieval ranking for non-normalized embeddings (Context). |
| Prompts (`backend/app/prompts/`) | — | None | No |
| CI jobs / gates | — | None | No |
| Internal service signatures (backend-only) | `QAService.answer_question(query, document_type, k_results=None, custom_prompt=None)`; `RerankService.answer_question(query, document_type, k_results=None, rerank_top_n=None, custom_prompt=None)` | `document_type` removed from both. Both add keyword-only `document_title: str` (required) and `metadata_filter: dict \| None = None`. | Internal. The only production caller is `document.py`. Positional test calls change: `qa_service_test.py:87,132`, `rerank_service_test.py:89,126`. |
| New internal function (backend-only) | — | `build_document_filter(document_title: str, metadata_filter: dict \| None = None) -> dict` in `backend/app/infrastructure/vector_db/filters.py` | No (new) |
| New internal score API (backend-only, F-031) | Only `similarity_search_with_score` exists, returning raw distance. | New `cosine_distance_to_similarity(distance: float) -> float` in `backend/app/infrastructure/vector_db/scoring.py`. New `similarity_search_with_relevance_scores(query, k=None, metadata_filter=None, where_document=None) -> list[tuple[Document, float]]` on both `VectorDBRepository` and `PGVectorDBRepository`. `similarity_search_with_score` is unchanged and still returns raw distance (AC-8). `ChromaDBClient.get_or_create_collection(name)` keeps its signature, creates with cosine and raises `RuntimeError` on a non-cosine collection. | No (additive). `/search` switches to the new method, so the router test mocks at `document_router_test.py:188,306-312` change. |

## Design

**Filter builder (new, one place).** Add a pure function in
`backend/app/infrastructure/vector_db/filters.py`:

```python
def build_document_filter(
    document_title: str,
    metadata_filter: dict | None = None,
) -> dict: ...
```

1. Clauses start as `[{"titulo": {"$eq": document_title}}]`.
2. If `metadata_filter` is non-empty:
   - a dict with one key (a field, `$and` or `$or`) is appended as one clause;
   - a dict with several field keys is split into one clause per key. Chroma rejects multi-key
     dicts; PGVector treats them as AND, so splitting keeps the meaning on both.
3. Return the single clause itself when there is one. With only the title, the result is the
   single top-level condition `{"titulo": {"$eq": document_title}}`, with no `$and`. Return
   `{"$and": clauses}` when there are two or more. Chroma rejects a one-element `$and`.

The builder never emits a `tipo_documento` clause (REQ-4). One appears only if the client's
`metadata_filter` contains it.

The title clause is always a top-level conjunct, so no client filter can widen the scope. A client
filter of `{"titulo": "other"}` yields an empty result.

The clauses the builder itself emits, and its `$and` wrapper, are valid on both backends (verified
above), so the repositories need no backend-specific translation. Client-supplied operators pass
through unchanged (OQ-2 decision (a)). Some exist on only one backend (`$not`, `$like`, `$ilike`,
`$between`, `$exists` are PGVector-only), so a client filter using them fails on Chroma (Non-goals).

**Services.**
- `QAService.answer_question` and `RerankService.answer_question` drop `document_type` and gain
  keyword-only `document_title` and `metadata_filter`.
- They set `search_kwargs["filter"] = build_document_filter(document_title, metadata_filter)`
  in place of the type-only filter at `qa_service.py:59` and `rerank_service.py:69`.
- Their log lines (`qa_service.py:52`, `rerank_service.py:59-62`) log the title in place of
  `doc_type=`.
- `k` and `where_document` stay as they are (REQ-6).

**Router.**
- `ask_question` stops passing `document_type="documento-pdf"` (`document.py:213,222`, together
  with the `TODO issue #15` comments). It passes `document_title=document_id` and
  `metadata_filter=request.metadata_filter` to whichever service it calls.
- `search_document` passes
  `metadata_filter=build_document_filter(document_id, request.metadata_filter)` to
  `vdb_repo.similarity_search_with_score`.
- `ingest_document` is unchanged.

**Repositories.**
- In both `similarity_search_with_score`, replace `metadata_filter or {...}` with
  `{...} if metadata_filter is None else metadata_filter`.
- A caller-supplied filter is never silently replaced; the router always supplies a non-empty one.
- The `None` default stays `{"tipo_documento": "documento-pdf"}`. It is unreachable from the API
  after this spec and is left to F-024 (Non-goals).
- Nothing else in the repositories changes.

**Alternatives considered.**
- *Keep the `tipo_documento` clause in the scope.* Rejected (OQ-1): once retrieval is title-scoped
  it adds no isolation. Its only effect is to hide documents ingested with a non-default type.
- *Per-backend filter translation inside each repository.* Rejected: one shape is already valid on
  both backends, so translation adds code with no benefit. F-012 can still push `where_document`
  into the repositories later.
- *`RetrievalQA`/LCEL retriever wrapper that post-filters by title.* Rejected: post-filtering after
  top-k returns fewer than k chunks and still ranks against foreign documents.
- *Scope by Postgres document UUID.* Rejected here: chunks carry no `document_id` and titles are not
  unique (F-002). `build_document_filter` is the single seam to change once F-002 lands.

### Search score (F-031)

**Conversion (new, one place).** Add `backend/app/infrastructure/vector_db/scoring.py`:

```python
COSINE_SPACE = "cosine"

def cosine_distance_to_similarity(distance: float) -> float:
    return min(1.0, max(0.0, 1.0 - distance))
```

Cosine distance lies in [0, 2], so `1 − d` lies in [−1, 1]. Clamping maps every distance ≥ 1
(orthogonal or opposite vectors) to 0. It also absorbs float noise just below 0. The function is
monotone non-increasing, so ascending distances give non-increasing scores, and the order is kept.

**Pin the metric.**
- Chroma:
  - In `chroma_client.py`, define the collection metadata once: `{"hnsw:space": COSINE_SPACE}`.
  - `ChromaDBClient.get_or_create_collection` passes it as `metadata=` to `create_collection`.
  - `VectorDBRepository` passes the same dict as `collection_metadata=` to `Chroma(...)`.
  - Both are needed. In unit tests (`document_scoping_test.py`) the `ChromaDBClient` is a mock, and
    `Chroma`'s own `get_or_create_collection` creates the collection.
  - The `hnsw:space` metadata key must be used, not `configuration`. On server 1.0.0 the metadata
    key is the only place the space is reported truthfully (Context), and the REQ-9 guard relies on
    it. AC-15 (c) pins it. It also keeps `langchain_chroma`'s `_select_relevance_score_fn`
    consistent (Context), although this spec does not use it.
- PGVector: `PGVectorStore.create_sync(..., distance_strategy=DistanceStrategy.COSINE_DISTANCE)`.
  This is the same value as the default, so no table, index or data changes.

**Refuse a legacy Chroma collection (REQ-9).** When `ChromaDBClient.get_or_create_collection` finds
the collection already exists, it reads the effective space:

1. `metadata["hnsw:space"]`, when present;
2. else `configuration_json["hnsw"]["space"]` (1.0.12 bindings shape);
3. else `configuration_json["hnsw_configuration"]["space"]` (server 1.0.0 shape);
4. else `"l2"`, Chroma's default when no metric is given (Context).

If the space is not `"cosine"`, it logs the error and raises `RuntimeError`. The message names the
collection, its space, and says to recreate it and re-ingest. It never deletes or modifies the
collection.

Why metadata comes first (amended 2026-10-15 after `/spec verify`):
- Server 1.0.0 always reports `hnsw_configuration.space == "l2"`, even for a cosine collection
  (Context, QA probe). The original order read `configuration_json` first, so the backend refused
  its own cosine collection after every backend restart.
- This code creates the collection with `metadata={"hnsw:space": "cosine"}` (AC-15 (c)). Through
  the 1.0.12 client, that key is honored at creation (QA probe) and cannot be changed afterwards
  (`CollectionCommon.py:508-514`).
- The `configuration_json` fallback cannot produce a false accept on either shape probed. Locally it
  reports the real space; on server 1.0.0 it only ever says `l2`, which is refused anyway.

Collections that are refused although they may be cosine (decided; refusal is the safe side, the
backend never modifies the collection, and the error tells the operator to recreate it):
- *`metadata` `None`, created with `configuration={"hnsw": {"space": "cosine"}}`.* On server 1.0.0
  its `configuration_json` says `l2`, so it cannot be told apart from an `l2` collection without
  querying it. **It is refused on server 1.0.0.** It is accepted where `configuration_json` reports
  the real space (1.0.12 local bindings, AC-16 (v)). This is not new: the approved order refused it
  on server 1.0.0 too. This code never creates such a collection.
- *`metadata={"hnsw:space": "l2"}` plus `configuration` cosine.* Locally its real space is cosine
  (Context). Metadata wins, so it is refused. This code never creates it. It is not pinned by an AC.

*Rejected alternative: probe the space by querying the collection.* It would need a query against
the operator's collection on every repository build and an embedding of the right dimension, to
resolve a case this code never creates. A read-only probe is used only in QA's AC-19 check.

The guard sits in the client wrapper that owns the collection lifecycle. `VectorDBRepository.__init__`
already calls it first (`repository.py:24`).

Fail rather than warn: with an `l2` collection, the clamp turns every typical distance (≫ 1)
into 0. `/search` would return 200 with meaningless scores, which is the silent failure this spec
removes.

**Repositories.** Each repository gets
`similarity_search_with_relevance_scores(query, k=None, metadata_filter=None, where_document=None)`.
It calls its own `similarity_search_with_score` with the same arguments, so it keeps the AC-8
filter defaults. It then maps each `(doc, d)` to `(doc, cosine_distance_to_similarity(d))`,
keeping the order. `similarity_search_with_score` itself is unchanged.

**Router.** `search_document` calls `vdb_repo.similarity_search_with_relevance_scores` in place of
`similarity_search_with_score` (`document.py:135`), with the same arguments. Nothing else changes:
- `SearchResultItem(score=...)` gets the converted value.
- `log_search` receives the converted tuples, so `avg_similarity_score` becomes a mean similarity
  (REQ-10) with no change in `InteractionService`.

**Setup script.** `backend/admin_chroma.py:64` creates `rag-docs` with
`metadata={"hnsw:space": "cosine"}`. Otherwise a manual setup would produce a collection the backend
refuses.

**Alternatives considered.**
- *LangChain `similarity_search_with_relevance_scores` on the store.* Rejected:
  - It does not clamp. It only warns on values outside [0, 1], so a cosine distance > 1 would
    yield a negative score that fails `ge=0.0` (a 500 again), plus a warning per request.
  - On Chroma its function comes from `metadata["hnsw:space"]` and silently falls back to L2 for a
    legacy collection.
  - An explicit function is one line and can be tested without a store.
- *Expose the distance honestly* (F-031 option 2: rename or drop `le=1.0`). Rejected by the user:
  `score` stays a similarity.
- *Auto-recreate a non-cosine collection.* Rejected: it silently drops data, and the default
  (OpenAI) configmap also uses Chroma.
- *Convert in the router.* Rejected: the metric is a repository concern.
- *Make the metric a `Setting`.* Rejected: there is no requirement for another metric, and it would
  add a configmap/template contract and a k8s task.

## Acceptance criteria

| ID | Given / When / Then | Verified by |
|---|---|---|
| AC-1 | Given these inputs to `build_document_filter`: (a) title only; (b) title + single-key `metadata_filter`; (c) title + multi-key `metadata_filter`; (d) title + `metadata_filter` that is a `$and` or `$or` expression; (e) title + `metadata_filter={"tipo_documento": "x"}`. Then for each, the output contains `{"titulo": {"$eq": <title>}}` as the whole filter or as a direct element of the top-level `$and`. It passes `chromadb.api.types.validate_where`. It passes `AsyncPGVectorStore._create_filter_clause` (instance via `object.__new__`) without raising. A `tipo_documento` key appears in the output for (e) only. | `backend/tests/unit/infrastructure/vector_db_filters_test.py` |
| AC-2 | Given title only and `metadata_filter` `None` or `{}`, the output is exactly `{"titulo": {"$eq": <title>}}`. There is no `$and` wrapper and no extra clause. | `backend/tests/unit/infrastructure/vector_db_filters_test.py` |
| AC-3 | Given `metadata_filter={"titulo": "other-doc"}` for title `doc-a`, the output still has `{"titulo": {"$eq": "doc-a"}}` as a top-level conjunct. | `backend/tests/unit/infrastructure/vector_db_filters_test.py` |
| AC-4 | When `QAService.answer_question(query, document_title="doc-a", metadata_filter=<f>)` runs, `as_retriever` receives `search_kwargs["filter"] == build_document_filter("doc-a", <f>)`, both for `<f>` `None` and for a non-empty `<f>`. `search_kwargs["where_document"] == {"$contains": " "}` is unchanged. | `backend/tests/unit/services/rag/qa_service_test.py` |
| AC-5 | Same as AC-4 for `RerankService.answer_question`. | `backend/tests/unit/services/rag/rerank_service_test.py` |
| AC-6 | When `POST /api/v1/documents/doc-a/ask` is called with `strategy` `standard`, and again with `rerank`, and `metadata_filter={"pagina": 1}`, the called service receives `document_title="doc-a"` and `metadata_filter={"pagina": 1}`, and no `document_type` argument. | `backend/tests/unit/api/document_router_test.py` |
| AC-7 | When `POST /api/v1/documents/doc-a/search` is called with `metadata_filter={}`, the repository's `similarity_search_with_relevance_scores` receives `metadata_filter == {"titulo": {"$eq": "doc-a"}}`. | `backend/tests/unit/api/document_router_test.py` |
| AC-8 | Given a caller-supplied non-`None` filter, both `VectorDBRepository` and `PGVectorDBRepository` `similarity_search_with_score` forward it unchanged as `filter=`. With `None`, both use `{"tipo_documento": "documento-pdf"}`. | `backend/tests/unit/infrastructure/vector_db_repository_test.py`, `backend/tests/unit/infrastructure/pgvector_repository_test.py` (new) |
| AC-9 | Given a deployed stack with two content-distinct PDFs A and B ingested under different titles, when `/search` is called on A with a query about content that exists only in B, then every result has `metadata.titulo` equal to A's title. Unscoped retrieval would surface B's chunks, so this scenario fails on `dev` @ `200c4cf`. A second query about A's content returns at least one result. | `behave backend/tests/behave/document_scoping.feature` (deployed stack) |
| AC-10 | Given the same two documents, when `/ask` (`strategy=standard`) is called on A with a question about content that exists only in B, then every `source_documents[].metadata.titulo` equals A's title. | `behave backend/tests/behave/document_scoping.feature` (deployed stack; live LLM) |
| AC-11 | Gates show no new errors beyond the baseline in `.claude/CLAUDE.md`. | `cd backend && uv run pytest tests/unit` → all pass (≥ 143 + new); `uv run ruff check app tests` → only the two baseline errors; `uv run ruff format --check app` and `uv run mypy app` → clean |
| AC-12 | Given the FastAPI app with these dependency overrides: a real `VectorDBRepository` over `chromadb.EphemeralClient` (telemetry off) with `DeterministicFakeEmbedding`; a real `QAService` over that repository with `FakeListLLM`; mocked document and interaction services; and every other endpoint dependency (`get_rerank_service`, `get_ingestion_service`, `get_db_session`) mocked as in `document_router_test.py` `setUp`, so no LLM client or Cohere setting is built. The store (a unique collection name per test) holds chunks of `doc-a` with `tipo_documento="custom-type"` and of `doc-b` with `tipo_documento="documento-pdf"`. They use the metadata keys `PDFTextExtractor.extract_with_metadata` sets, and each chunk's `page_content` contains a space, so `where_document={"$contains": " "}` keeps it. When `POST /api/v1/documents/doc-a/search` and `POST /api/v1/documents/doc-a/ask` (`strategy=standard`) are called with a query matching both documents' text, then both return 200 with at least one result or source, and every `metadata.titulo` is `doc-a`. This fails on `dev` @ `200c4cf`, where the same setup returns only `doc-b`'s chunk (probe executed, see Context). No network or live LLM is used. | `backend/tests/unit/api/document_scoping_test.py` (new) |

| AC-13 | `cosine_distance_to_similarity` maps 0.0 → 1.0, 0.25 → 0.75, 1.0 → 0.0, 1.708 → 0.0, 2.0 → 0.0 and -1e-7 → 1.0 (within `assertAlmostEqual` default places). For distances ascending over [0, 2] the outputs are non-increasing and all in [0, 1]. | `backend/tests/unit/infrastructure/vector_db_scoring_test.py` (new) |
| AC-14 | Given a mocked store whose `similarity_search_with_score` returns distances `[0.3, 1.708]`, both `VectorDBRepository` and `PGVectorDBRepository` `similarity_search_with_relevance_scores(query="q", k=2, metadata_filter=f)` return the same documents in the same order, with scores `[0.7, 0.0]` (almost-equal). The store receives the same arguments AC-8 specifies for `similarity_search_with_score` (`filter=f` unchanged; Chroma `where_document={"$contains": " "}`, PGVector `where_document=None`). | `backend/tests/unit/infrastructure/vector_db_repository_test.py`, `backend/tests/unit/infrastructure/pgvector_repository_test.py` |
| AC-15 | The cosine metric is pinned: (a) `VectorDBRepository` constructs `Chroma` with `collection_metadata={"hnsw:space": "cosine"}`; (b) `PGVectorStore.create_sync` is called with `distance_strategy=DistanceStrategy.COSINE_DISTANCE`; (c) a `ChromaDBClient` whose `chromadb.HttpClient` is patched to return a `chromadb.EphemeralClient` (telemetry off), with no such collection, makes `get_or_create_collection(name)` create one whose `metadata == {"hnsw:space": "cosine"}` and whose `configuration_json["hnsw"]["space"] == "cosine"`. The `metadata` assertion is what keeps the guard working on server 1.0.0 (Design). | `backend/tests/unit/infrastructure/vector_db_repository_test.py`, `backend/tests/unit/infrastructure/pgvector_repository_test.py`, `backend/tests/unit/infrastructure/chroma_client_test.py` |
| AC-16 | `ChromaDBClient.get_or_create_collection(name)` on an existing collection. **Refused** (raises `RuntimeError` whose message contains the collection name, `l2` and `recreate`): (i) `EphemeralClient` collection pre-created with `metadata={"hnsw:space": "l2"}`; (ii) `EphemeralClient` collection pre-created with no metadata; (iii) mocked `get_collection` returning `metadata=None` and `configuration_json={"hnsw_configuration": {"space": "l2"}}` (server 1.0.0, no metric). After (i) and (ii) the collection still exists with its original space and item count. **Accepted** (does not raise): (iv) `EphemeralClient` collection pre-created with `metadata={"hnsw:space": "cosine"}`; (v) mocked `metadata=None` with `configuration_json={"hnsw_configuration": {"space": "cosine"}}` (configuration-only cosine, truthful configuration; server 1.0.0 never returns this); (vi) mocked `metadata={"hnsw:space": "cosine"}` with `configuration_json={"_type": "CollectionConfigurationInternal", "hnsw_configuration": {"space": "l2"}}`, the shape server 1.0.0 returned live for a collection this code created. | `backend/tests/unit/infrastructure/chroma_client_test.py` |
| AC-17 | Given the FastAPI app with dependency overrides as in AC-12, a real `VectorDBRepository` over `chromadb.EphemeralClient` (unique collection, cosine via the repository) with `DeterministicFakeEmbedding`, and chunks of `doc-a` with distinct texts, each containing a space. The test first asserts that the repository's raw `similarity_search_with_score` returns at least one distance > 1 for the chosen off-topic query and the `doc-a` scope, so the clamp is exercised. When `POST /api/v1/documents/doc-a/search` is called with that query and `k_results` equal to the number of chunks, then the response is 200; every `score` is in [0, 1]; scores are non-increasing; and, with `get_by_title` returning a document, the mocked `interaction_service.log_search` receives `results` whose scores equal the response scores, in order. This fails before T-4 (500). No network, no live LLM. | `backend/tests/unit/api/search_score_test.py` (new) |
| AC-18 | The response-model bound is kept. `backend/app/models/responses/search_response.py` and the bound tests `responses_test.py:136-152` are unchanged, and the tests pass. | `git diff 200c4cf -- backend/app/models/responses/search_response.py backend/tests/unit/models/responses_test.py` → empty; `uv run pytest tests/unit/models/responses_test.py` → pass |
| AC-19 | On the deployed stack (`local,chroma`, server 1.0.0), after the verify procedure below: (a) the collection `rag-docs` has `metadata == {"hnsw:space": "cosine"}`; (b) it computes cosine distances: querying with twice a stored embedding `e` returns a top distance whose absolute value is < 1e-3 (float noise can make it slightly negative), while the `l2` distance for the same query, `\|e\|²`, is > 1e-2, so the check tells the two metrics apart; (c) after a backend-only restart against that existing collection, the backend accepts it: `/search` on an ingested document returns 200. `configuration_json` is recorded but not asserted (server 1.0.0 always reports `l2`, Context). | (a), (b): the AC-19 probe in the verify procedure prints `metadata`, `configuration_json`, `top_distance` and `l2_alternative`; QA records all four in *Verification*. (c): verify procedure step 5, `curl` → `200`. |

**Verify procedure (deployed stack).** An existing collection is not converted (REQ-9), so QA
recreates it before AC-9, AC-10 and AC-19:

1. `kubectl rollout restart deployment/chromadb`, and wait for it to become ready. The pod has no
   volume, so the collection is gone.
2. `kubectl rollout restart deployment/rag-docs-backend`, and wait. This drops the cached repository.
3. Run `behave backend/tests/behave/document_scoping.feature`. It uploads both PDFs; ingestion
   re-runs because the vector store no longer has them.
4. Run the AC-19 probe (a, b). It only reads: one `get` and one `query`, nothing is written. The
   block below is indented 3 spaces in the raw file; remove that indent before pasting, or the
   heredoc never terminates and Python raises an indentation error.

   ```bash
   kubectl port-forward deploy/chromadb 8000:8000   # separate terminal
   cd backend && uv run python - <<'EOF'
   import chromadb
   c = chromadb.HttpClient(host="localhost", port=8000, tenant="dev", database="rag-database")
   col = c.get_collection("rag-docs")
   print("metadata", col.metadata)
   print("configuration_json", col.configuration_json)
   e = [float(x) for x in col.get(limit=1, include=["embeddings"])["embeddings"][0]]
   r = col.query(query_embeddings=[[2 * x for x in e]], n_results=1, include=["distances"])
   print("top_distance", r["distances"][0][0])        # cosine: ~0
   print("l2_alternative", sum(x * x for x in e))     # squared L2 to e: |e|^2
   EOF
   ```

   Pass: `metadata` is `{'hnsw:space': 'cosine'}`, `abs(top_distance)` < 1e-3, `l2_alternative` > 1e-2.
   Checked offline against `EphemeralClient` (2026-10-15): a cosine collection gave `top_distance`
   -1.2e-7 and an `l2` one gave `top_distance` equal to `l2_alternative` (0.5825).
5. Restart `rag-docs-backend` again, but not Chroma. This is the first time the REQ-9 guard reads an
   *existing* collection on server 1.0.0; in step 3 the collection was missing and was created. A
   wrong read makes every vector request fail after any backend restart (the 2026-10-15 failure).
   - AC-19 (c), no LLM: with the backend port-forwarded on 8106,
     `curl -s -o /dev/null -w '%{http_code}' -X POST http://localhost:8106/api/v1/documents/<title A>/search -H 'Content-Type: application/json' -d '{"query": "<any>"}'`
     → `200`.
   - Re-run `document_scoping.feature`. It must pass.

AC-9 passing (200 on `/search`) is the live evidence for REQ-7. AC-10 is re-run because the metric
change can change `/ask` ranking (Context).

Rerank and non-default types: `CohereRerank` needs the network, so AC-12 does not cover
`strategy=rerank`. That path is covered only by AC-5 (the retriever gets the same title-only filter)
and AC-6 (the router passes no `document_type`).

## Tasks

| ID | Task | Agent | Depends on | Files | Status |
|---|---|---|---|---|---|
| T-1 | Add `build_document_filter(document_title, metadata_filter=None)`. Use it in `QAService`, `RerankService` and the `/search` handler. Remove `document_type` from both `answer_question` signatures and from the `/ask` calls (`document.py:211-224`, including the `TODO issue #15` comments). Pass `document_title`/`metadata_filter` through. Log the title instead of `doc_type` (`qa_service.py:52`, `rerank_service.py:59-62`). Replace `or` with an `is None` default in both repositories, keeping the `tipo_documento` default value. Update the `metadata_filter` `Field` descriptions. Update the existing positional `answer_question` test calls (`qa_service_test.py:87,132`, `rerank_service_test.py:89,126`). Add or adjust unit tests for AC-1 to AC-8 and AC-12. Leave ingestion untouched. | backend-agent | — | `backend/app/infrastructure/vector_db/filters.py` (new), `backend/app/infrastructure/vector_db/repository.py`, `backend/app/infrastructure/vector_db/pgvector_repository.py`, `backend/app/services/rag/qa_service.py`, `backend/app/services/rag/rerank_service.py`, `backend/app/api/routers/v1/document.py`, `backend/app/models/requests/search_request.py`, `backend/tests/unit/infrastructure/vector_db_filters_test.py` (new), `backend/tests/unit/infrastructure/pgvector_repository_test.py` (new), `backend/tests/unit/infrastructure/vector_db_repository_test.py`, `backend/tests/unit/services/rag/qa_service_test.py`, `backend/tests/unit/services/rag/rerank_service_test.py`, `backend/tests/unit/api/document_router_test.py`, `backend/tests/unit/api/document_scoping_test.py` (new) | Done |
| T-2 | Add a behave feature for AC-9 and AC-10 with a second, content-distinct PDF fixture. Use queries that target content only in the *other* document, so the scenario fails without the fix. Do not reuse the same PDF under a second title: that path depends on F-002's dedup behavior. **Reopened 2026-10-15: replace the fixture with a short PDF.** The user replaces `us-constitution.pdf` (untracked) with a short (1–3 page) PDF unrelated to ROS. Delete `us-constitution.pdf`, add the new PDF, and update its entry in `SOURCES.md` (source and license). Rewrite the Background step and the cross-document queries (`document_scoping.feature:11,14,21`) so that they target content found only in the new PDF and not in `ros-intro.pdf`. Keep the in-document query on `ros-intro`. | qa-agent | T-1; the user's PDF | `backend/tests/behave/document_scoping.feature`, `backend/tests/behave/steps/document_scoping_steps.py` (only if needed), `backend/tests/behave/data/us-public-law-117-52.pdf` (new), `backend/tests/behave/data/us-constitution.pdf` (delete), `backend/tests/behave/data/SOURCES.md` | Done |
| T-3 | Update `docs/reference/architecture.md` (§ Vector Database Storage, § API Endpoints). State that retrieval is scoped by `titulo` only, that `metadata_filter` is AND-ed with it, and that `document_type` is stored but not used for retrieval. | architect | T-1 | `docs/reference/architecture.md` | Done |
| T-4 | F-031 (Design § Search score). Add `scoring.py` with `COSINE_SPACE` and `cosine_distance_to_similarity`. In `ChromaDBClient.get_or_create_collection`, create with `{"hnsw:space": "cosine"}` and raise `RuntimeError` on an existing non-cosine collection (REQ-9). Pass the same dict as `collection_metadata` to `Chroma(...)`. Pass `distance_strategy=DistanceStrategy.COSINE_DISTANCE` (from `langchain_postgres.v2.indexes`) to `create_sync`. Add `similarity_search_with_relevance_scores` to both repositories, and switch `search_document` to it. Make `admin_chroma.py:64` create the collection with cosine metadata. Update existing tests: the router mocks (`document_router_test.py:188,306-312`, AC-7) and any `chroma_client_test.py`/`vector_db_repository_test.py` setup that the new guard or `collection_metadata` breaks (mock collections must report cosine). Replace the stale L2 comment at `document_scoping_test.py:27`. Fix "cosine similarity calculations" in `tests/fixtures/README.md:23`, which describes raw distances in the golden files. Add tests for AC-13 to AC-17. Leave `search_response.py`, `responses_test.py` and `similarity_search_with_score` unchanged (AC-8, AC-18). | backend-agent | T-1 | `backend/app/infrastructure/vector_db/scoring.py` (new), `backend/app/infrastructure/vector_db/chroma_client.py`, `backend/app/infrastructure/vector_db/repository.py`, `backend/app/infrastructure/vector_db/pgvector_repository.py`, `backend/app/api/routers/v1/document.py`, `backend/admin_chroma.py`, `backend/tests/unit/infrastructure/vector_db_scoring_test.py` (new), `backend/tests/unit/infrastructure/chroma_client_test.py`, `backend/tests/unit/infrastructure/vector_db_repository_test.py`, `backend/tests/unit/infrastructure/pgvector_repository_test.py`, `backend/tests/unit/api/document_router_test.py`, `backend/tests/unit/api/document_scoping_test.py`, `backend/tests/unit/api/search_score_test.py` (new), `backend/tests/fixtures/README.md` | Done |
| T-5 | Document score semantics in `docs/reference/architecture.md`: `/search` `score` is cosine similarity in [0, 1], higher is better (§ API Endpoints, `:198`); `avg_similarity_score` is the mean of those scores, and rows from before SPEC-001 hold distances (§ DB schema, `:159`); both vector backends use cosine, and an existing non-cosine Chroma collection must be recreated (§ Vector Database Storage). | architect | T-4 | `docs/reference/architecture.md` | Done |
| T-6 | Correct the REQ-9 guard's read order (Design § Refuse a legacy Chroma collection). `ChromaDBClient._effective_space` reads `metadata["hnsw:space"]` first, then `configuration_json["hnsw"]["space"]`, then `configuration_json["hnsw_configuration"]["space"]`, else `"l2"`. Creation and the error message are unchanged. In `chroma_client_test.py`: add the AC-16 (vi) case (metadata cosine + server 1.0.0 `hnsw_configuration` `l2` → accepted); relabel the existing `test_server_1_0_0_shape_cosine_is_accepted` as the configuration-only cosine case (AC-16 (v)), since server 1.0.0 never returns that shape; let the mocked-collection helper take `metadata`; add the `metadata == {"hnsw:space": "cosine"}` assertion to `test_creates_cosine_collection` (AC-15 (c)). Check the case first fails on the current guard. Gates as AC-11. | backend-agent | T-4 | `backend/app/infrastructure/vector_db/chroma_client.py`, `backend/tests/unit/infrastructure/chroma_client_test.py` | Done |

Backend coverage:
- AC-9 and AC-10 run against whichever vector backend the deployed stack uses (Chroma under the
  `local` profile).
- PGVector is covered at unit level only:
  - AC-1: filter grammar.
  - AC-8: repository pass-through.
  - AC-14: score conversion.
  - AC-15 (b): pinned metric.
- AC-12 and AC-17 run on an in-memory Chroma.

QA's `/spec verify` runs the verify procedure under *Acceptance criteria* (recreate Chroma, restart
the backend), then re-runs AC-9 and AC-10 and runs AC-19. No new behave scenario is needed: T-2's
`/search` step already asserts 200 (`backend/tests/behave/steps/document_scoping_steps.py:41`), and a
200 means every `score` passed `SearchResultItem`'s bounds.

No frontend, k8s or ci task:
- No API schema, setting, manifest or workflow changes.
- No frontend task: the frontend never calls `/search` (Contracts).
- No k8s task:
  - The Chroma entrypoint creates no collection, and the pod has no volume (Context).
  - The metric is not a setting.
  - Recreating the collection is a `kubectl rollout restart`, which is QA's verify step and not a
    manifest change.
- `docs/guides/` and `docs/development/` do not describe `metadata_filter`, retrieval filtering or
  `document_type`. Checked with
  `grep -rn 'metadata_filter\|tipo_documento\|document_type\|documento-pdf' docs/guides docs/development`:
  no match.
- They do not describe scores or metrics either. Checked with
  `grep -rni 'score\|similarity\|distance\|cosine\|hnsw' docs/guides docs/development`: no match.
- `docs/guides/setup.md:97-101` points to `admin_chroma.py` for tenant and database setup. Its text
  stays correct after T-4.
- In `docs/reference/` the only hit for `document_type` is the `documents.document_type` column
  (`architecture.md:143`), which does not change. The score hits (`architecture.md:159,198`) are
  covered by T-5.

T-6 (added 2026-10-15) corrects the REQ-9 guard after `/spec verify` failed on server 1.0.0. It
changes no requirement or contract, and `docs/reference/architecture.md` § Vector Database Storage
stays correct: it says that a non-cosine collection is refused, not how the space is read.

## Open questions

- [x] **OQ-1: Keep the `tipo_documento` clause in the scope?** Decided (user, 2026-10-15): **(b)
  drop it.** The scope is the document title plus the optional client `metadata_filter`. REQ-4 is
  rewritten, `build_document_filter` loses its `document_type` parameter, and `document_type` is
  removed from both `answer_question` methods. Ingestion is unchanged. AC-12 proves a non-default
  type is retrievable. What remains of F-024 is listed in Non-goals.
- [x] **OQ-2: Validate client `metadata_filter` keys?** Decided (user, 2026-10-15): **(a) pass it
  through**, AND-ed with the scope, without validation. Error mapping for bad filters stays with
  F-007 (Non-goals).
- [x] **OQ-3: Ship title scoping now, or wait for F-002 (#20) to settle the document identity?**
  Decided (user, 2026-10-15): **ship now.** `build_document_filter` is the single seam F-002 would
  change.

## Verification

Verified by `qa-agent` on 2026-10-15 against the uncommitted working tree on
`spec/SPEC-001-scope-retrieval-to-document` (base `200c4cf`). Unit commands run from `backend/`.
Live stack: minikube, `skaffold run -p local,chroma -f skaffold.yaml` from the working tree, then the
verify procedure (steps 1-5) exactly as written. The running pod was checked to contain
`_effective_space` (`kubectl exec deploy/rag-docs-backend -- grep -c _effective_space ...` -> 2).

| AC | Result | Evidence |
|---|---|---|
| AC-1 | Pass | `uv run --extra dev pytest tests/unit/infrastructure/vector_db_filters_test.py` -> 4 passed (subTests cover shapes a-e through `validate_where` and `_create_filter_clause`) |
| AC-2 | Pass | same file -> `test_title_only_is_single_condition_without_and` passed |
| AC-3 | Pass | same file -> `test_client_filter_cannot_replace_title_scope` passed |
| AC-4 | Pass | `pytest tests/unit/services/rag/qa_service_test.py` -> 3 passed (incl. `test_answer_question_scopes_retriever_to_document`) |
| AC-5 | Pass | `pytest tests/unit/services/rag/rerank_service_test.py` -> 3 passed |
| AC-6 | Pass | `pytest tests/unit/api/document_router_test.py` -> 13 passed (incl. `test_ask_passes_document_scope_to_service`) |
| AC-7 | Pass | same file -> `test_search_scopes_filter_to_document` passed |
| AC-8 | Pass | `pytest tests/unit/infrastructure/vector_db_repository_test.py tests/unit/infrastructure/pgvector_repository_test.py` -> 8 + 2 passed |
| AC-9 | Pass | Step 3 (fresh Chroma + backend restarted): `cd backend/tests/behave && uv run behave document_scoping.feature` -> 2 scenarios, 17 steps passed. Cross-document query "What does the Highway Trust Fund expenditure authority extension change to December 4, 2021?" on `ros-intro` -> every `titulo` is `ros-intro`. Positive control, same query on `us-public-law-117-52` -> 4 results, scores 0.695/0.546/0.531/0.495 (on `ros-intro` the best score is 0.169), so unscoped top-k would surface the law's chunks. `What is ROS?` on `ros-intro` -> results, all `ros-intro`. Re-run after step 5 (existing collection) -> also 2 scenarios passed. Not run on `dev` @ `200c4cf` (no checkout allowed); the failure on `dev` is inferred from the control scores. |
| AC-10 | Pass | Same runs: scenario "Standard ask is scoped" passed (live Ollama LLM), all `source_documents[].metadata.titulo` == `ros-intro`, before and after the step 5 restart |
| AC-11 | Pass | `uv run --extra dev pytest tests/unit -q` -> 154 passed; `ruff check app tests` -> only the 2 baseline errors (E501 `document_qa_steps.py:52`, F841 `document_service_test.py:155`); `ruff format --check app tests` -> 92 files already formatted; `mypy app` -> no issues in 53 files; `ruff check tests/behave` -> only baseline E501; `ruff format --check tests/behave` clean |
| AC-12 | Pass | `pytest tests/unit/api/document_scoping_test.py` -> 2 passed |
| AC-13 | Pass | `pytest tests/unit/infrastructure/vector_db_scoring_test.py` -> 2 passed |
| AC-14 | Pass | `vector_db_repository_test.py` (`test_relevance_scores_convert_distance_to_similarity`) and `pgvector_repository_test.py` -> passed |
| AC-15 | Pass | (a) `vector_db_repository_test.py:48` asserts `collection_metadata={"hnsw:space": "cosine"}`; (b) `pgvector_repository_test.py:58` asserts `DistanceStrategy.COSINE_DISTANCE`; (c) `chroma_client_test.py::test_creates_cosine_collection` asserts `metadata == {"hnsw:space": "cosine"}` and `configuration_json["hnsw"]["space"] == "cosine"` -> all passed (`chroma_client_test.py` 11 passed) |
| AC-16 | Pass | `pytest tests/unit/infrastructure/chroma_client_test.py -v`: (i) `test_existing_l2_collection_is_refused_and_untouched` (message has name, `l2`, `recreate`; space and count unchanged); (ii) `test_existing_collection_without_metadata_is_refused`; (iii) `test_server_1_0_0_shape_l2_is_refused`; (iv) `test_existing_cosine_collection_is_accepted`; (v) `test_configuration_only_cosine_is_accepted`; (vi) `test_server_1_0_0_metadata_cosine_with_l2_configuration_is_accepted` -> all PASSED. Note: (iii) asserts only that `RuntimeError` is raised, not the message text (the guard builds one message for every refusal; read in `chroma_client.py`). |
| AC-17 | Pass | `pytest tests/unit/api/search_score_test.py` -> 1 passed |
| AC-18 | Pass | `git diff 200c4cf -- backend/app/models/responses backend/tests/unit/models` -> empty; `pytest tests/unit/models/responses_test.py` -> 30 passed |
| AC-19 | Pass | Step 4 probe (verbatim, indent stripped; Chroma port-forwarded on 8000), output: `metadata {'hnsw:space': 'cosine'}`; `configuration_json {'_type': 'CollectionConfigurationInternal', 'hnsw_configuration': {..., 'space': 'l2', ...}}` (recorded, not asserted); `top_distance 0.0`; `l2_alternative 1.0000001341586882`. (a) pass, (b) pass: abs(0.0) < 1e-3 and 1.0 > 1e-2. Step 5 (`kubectl rollout restart deployment/rag-docs-backend` only): backend log `Collection 'rag-docs' exists` and `VectorDB repository initialized`; `curl -s -o /dev/null -w '%{http_code}' -X POST http://localhost:8106/api/v1/documents/us-public-law-117-52/search -H 'Content-Type: application/json' -d '{"query": "highway trust fund"}'` -> `200`; `document_scoping.feature` re-run -> 2 scenarios passed. (c) pass. |

Full behave suite (CI env vars and port-forwards from `integration-test.yml`, after the step 5 restart):
5 features passed, 1 failed; 7 scenarios passed, 1 failed; 54 steps passed, 1 failed, 1 skipped.
The failure is `document_qa_rerank.feature:7` (`/ask` rerank returns 500). Backend log:
`UnauthorizedError - status_code: 401 ... Incorrect API key provided` from Cohere. Classification:
environment (dummy Cohere key in the local cluster), not SPEC-001; the rerank path is covered by
AC-5 and AC-6 at unit level (see *Acceptance criteria*). I did not run that feature on `dev`, so
"pre-existing" is inferred from the 401, not measured.

Diff review (`git diff 200c4cf --stat` plus untracked files): all changed paths belong to
backend-agent (`backend/app`, `backend/admin_chroma.py`, backend unit tests, `backend/tests/fixtures/README.md`),
qa-agent (`backend/tests/behave/**`) or architect (`docs/`). Every file maps to T-1..T-6; no contract
change is missing from the *Contracts* table; no workflow, manifest, migration or `Settings` change.
`search_response.py` and `responses_test.py` are untouched.

## Changelog

- 2026-10-15: Draft created.
- 2026-10-15: Amended with the user's decisions on OQ-1 (drop `tipo_documento` from the scope),
  OQ-2 (pass `metadata_filter` through, no validation) and OQ-3 (ship now).
  - **Requirements changed**: REQ-4 is reversed. Retrieval no longer filters on `tipo_documento`.
    REQ-5 now covers REQ-4 and states that there is no validation. A goal was added.
  - **Contracts changed**:
    - `document_type` is no longer used for retrieval, so `/search` and `/ask` behave differently for documents with a non-default type.
    - `document_type` is removed from both `answer_question` signatures.
    - `build_document_filter` loses its `document_type` parameter.
  - **ACs and tasks**:
    - AC-1, AC-4, AC-6 and AC-7 were updated, and AC-12 was added (in-memory Chroma, non-default type).
    - T-1 and T-3 were widened.
    - The F-024 remainder is recorded in Non-goals.
  - **Needs user re-approval.**
- 2026-10-15: Approved by the user. Implementation started (T-1).
- 2026-10-15: T-1 done (backend-agent). Gates: baseline ruff errors only, mypy clean, 143 unit tests passed. AC-12 test verified to fail on `dev` @ 200c4cf (returns `doc-b`). Uncommitted.
- 2026-10-15: T-2 done (qa-agent): `document_scoping.feature` + `us-constitution.pdf` (public domain, see `backend/tests/behave/data/SOURCES.md`). Live run on minikube (`local,chroma`): AC-10 passes; AC-9 blocked by F-031 (`/search` 500, score 1.708 > `le=1.0`). Uncommitted.
- 2026-10-15: Amended to fold in [F-031](../findings/F-031-search-score-is-unbounded-distance.md),
  which blocks AC-9. The user decided: fold it in; `score` stays a similarity in [0, 1] (higher is
  better); cosine on both backends; recreating the Chroma collection and re-ingesting is acceptable.
  - **Title**: now "Scope retrieval to the requested document and return true similarity scores".
    The slug and branch are unchanged.
  - **Context**: added a "Search score is a distance" section, with Chroma, PGVector and LangChain
    facts. Probes were executed with chromadb 1.0.12, plus a read-only `GET` on the live 1.0.0
    server: the collection is `l2`, and the server shape is `hnsw_configuration`.
  - **Goals and Non-goals**: two goals added. Non-goals added for metric configurability, in-place
    collection migration, `avg_similarity_score` backfill, `/ask` scores, golden fixtures and
    startup construction (F-014).
  - **Requirements changed**: added REQ-7 (score is clamped cosine similarity, order kept), REQ-8
    (cosine pinned on both backends), REQ-9 (refuse an existing non-cosine Chroma collection) and
    REQ-10 (`avg_similarity_score` is a mean similarity).
  - **Contracts changed**:
    - `/search` `score` semantics: from raw distance to similarity; the schema is unchanged.
    - `/search` no longer returns 500 for distances > 1.
    - `search_interactions.avg_similarity_score` meaning changes; no backfill.
    - The Chroma collection metric is now cosine. Existing collections must be recreated and their
      documents re-ingested.
    - PGVector `distance_strategy` is explicit, with the same value as the default.
    - New internal score API.
    - No Settings, configmap, entrypoint or schema change.
  - **ACs**:
    - AC-7 now names `similarity_search_with_relevance_scores`.
    - AC-11's test floor is now ≥ 143.
    - AC-13 to AC-19 added.
    - AC-16 covers the server 1.0.0 `hnsw_configuration` shape. AC-18 diffs against Base `200c4cf`.
    - A verify procedure was added: recreate Chroma, restart the backend, re-run AC-9 and AC-10, then
      restart the backend again to exercise the REQ-9 guard on an existing collection.
  - **Tasks**: added T-4 (backend-agent) and T-5 (architect, `architecture.md`). T-1 to T-3 are
    unchanged. No k8s, frontend or ci task (reasons under *Tasks*).
  - **Needs user re-approval** (requirements and contracts changed). Status stays `In progress`:
    T-1 and T-2 are done and unaffected, and T-4 must not start before re-approval.
- 2026-10-15: F-031 amendment (REQ-7..10, AC-13..19, T-4, T-5) re-approved by the user, including the architect's four decisions. T-4 started.
- 2026-10-15: T-4 done (backend-agent). Gates: baseline ruff errors only, mypy clean, 153 unit tests passed. T-3 and T-5 started. Uncommitted.
- 2026-10-15: T-3 and T-5 done (architect, `docs/reference/architecture.md`). All tasks done; status In review. Uncommitted.
- 2026-10-15: Verified (qa-agent). Unit ACs, gates and AC-18 pass. AC-9, AC-10 and AC-19 fail on the deployed stack: server 1.0.0 reports `l2` in `configuration_json` for a collection created with `hnsw:space: cosine` metadata, so the REQ-9 guard refuses it after a backend restart (details under Verification). Remains In review.
- 2026-10-15: Amended after the failed `/spec verify` (architect). Server 1.0.0 always reports
  `configuration_json.hnsw_configuration.space == "l2"`, but it computes cosine for a collection
  created with `hnsw:space` metadata (QA probe). The REQ-9 guard read `configuration_json` first, so
  it refused the backend's own collection after every backend restart.
  - **Context**: QA's server 1.0.0 probe and a 1.0.12 local probe added. The row that cited
    `configuration_json: l2` as evidence of the space now cites the no-metric probe. "Metadata
    honored at creation on 1.0.0" moved from assumed to verified. Client-side `modify` refusal
    of `hnsw:space` added.
  - **Design**: the guard reads `metadata["hnsw:space"]` first, then `configuration_json` (`hnsw`,
    then `hnsw_configuration`), else `l2`. Decided: a collection with `metadata` `None` created
    through `configuration` cosine is refused on server 1.0.0, as it already was under the approved
    order. One outcome flips: a collection with metadata `l2` plus configuration cosine, which
    this code never creates, was accepted and is now refused. The verify-procedure fallback
    ("also pass `configuration=`") is removed; QA showed it does not change the report.
  - **ACs**: AC-15 (c) also asserts `metadata == {"hnsw:space": "cosine"}`. AC-16 adds case (vi),
    metadata cosine with server 1.0.0 `hnsw_configuration` `l2`, accepted; the `l2` cases stay
    refused. AC-19 no longer asserts `configuration_json`. It now asserts the metadata, a read-only
    cosine-distance probe, and that the backend accepts the existing collection after a restart.
    Verify procedure steps 4 and 5 updated. AC-9 and AC-10 are unchanged (already generic about the
    PDFs).
  - **Tasks**: T-6 added (backend-agent, guard order and tests). T-2 reopened to `Todo`: replace
    `us-constitution.pdf` with the user's short PDF and retarget the cross-document queries
    (blocked on the user's PDF). T-4 stays `Done`.
  - **Requirements and Contracts unchanged** (REQ-9 text and intent, every Contracts row). No
    user re-approval needed. Status should go back to `In progress` (main session).
- 2026-10-15: Back to In progress after QA verify (guard precedence, fixture swap). T-6 started.
- 2026-10-15: T-6 done (backend-agent): AC-16 (vi) failed on the old guard, passes now; 154 unit tests passed. T-2 (fixture swap) started. Uncommitted.
- 2026-10-15: T-2 done (qa-agent): `us-constitution.pdf` (52 pages) replaced by `us-public-law-117-52.pdf` (2 pages, public domain, GPO; see `backend/tests/behave/data/SOURCES.md`). `document_scoping.feature` cross-document queries now target the Highway Trust Fund text found only in the new PDF.
- 2026-10-15: Verified (qa-agent). AC-1..AC-19 all Pass, including the full verify procedure on minikube (`local,chroma`) with the step 5 backend-only restart. Full behave suite: only `document_qa_rerank.feature:7` fails (Cohere 401, environment). F-001 and F-031 -> `Fixed (SPEC-001)`. Status Done. Uncommitted.
