# F-031: `/search` score is a distance, but the response model requires a similarity in [0, 1]

| Field | Value |
|---|---|
| Severity | Medium |
| Category | correctness |
| Status | Fixed (SPEC-001) |
| Verification | Confirmed. Reproduced against mocked dependencies; the vector-store semantics were checked in the installed library source. Re-confirmed on 2026-10-15 by the architect in the SPEC-001 working tree. Re-read `search_response.py:8`, `document.py:135-162`, `repository.py:27-31,59-64`, `pgvector_repository.py:41-47,72-77` and `chroma_client.py:36`. In-process probes with chromadb 1.0.12: a collection created without a metric is `l2`, and `get_or_create_collection` with cosine metadata does not change an existing `l2` collection. Observed live by `qa-agent` during SPEC-001 T-2: a 500 with score 1.708. A read-only `GET` of the deployed collection (`chromadb/chroma:1.0.0`) returned `metadata: null` and `configuration_json.hnsw_configuration.space: "l2"`, so that score was a squared L2 distance. See [SPEC-001](../specs/SPEC-001-scope-retrieval-to-document.md). |
| Tracking issue | — |
| Found | 2026-10-15. Reported by `backend-agent` during SPEC-001 T-1. Folded into [SPEC-001](../specs/SPEC-001-scope-retrieval-to-document.md) on 2026-10-15 (REQ-7 to REQ-10, T-4), because it blocks AC-9. |

## Problem

`SearchResultItem.score` is declared as `ge=0.0, le=1.0` and described as "Similarity score". `/search` copies the second element of each `(Document, score)` tuple from `similarity_search_with_score` into that field unchanged. Neither backend returns a similarity there:

- **Chroma**: `langchain_chroma` returns the raw collection distance, where lower means more similar. This repo never configures the collection's distance function, so the metric is whatever Chroma uses by default.
  - Squared L2 is at most 4 on unit vectors and unbounded otherwise.
  - Cosine distance ranges over [0, 2].
- **PGVector**: `PGVectorStore` is built without `distance_strategy`, so it defaults to `COSINE_DISTANCE` and returns the raw `distance` column, in the range [0, 2].

When a hit's distance is greater than 1, constructing `SearchResultItem` raises a pydantic `ValidationError`. The generic handler then turns it into a 500. That happens when the query is unrelated to the document, or when the embeddings are not normalized under L2. When no hit exceeds 1, the endpoint returns 200, but the value means the opposite of its documented meaning: a lower score is a better match.

The same distance is stored as `search_interactions.avg_similarity_score`. That column is a mean distance with a similarity name.

## Evidence

Lines are cited at `dev` @ `200c4cf`. The `/search` score path is unchanged in the SPEC-001 working tree.

- `backend/app/models/responses/search_response.py:8`: `score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")`.
- `backend/app/api/routers/v1/document.py:134-138`: calls `vdb_repo.similarity_search_with_score`.
- `document.py:143-145`: `SearchResultItem(..., score=float(score), ...)`, with no conversion.
- `document.py:172-177`: `except Exception` turns the `ValidationError` into a 500 and puts the pydantic message in `detail` (see F-007).
- Validation fails before `log_search` (`document.py:155`), so failed searches are never logged.
- `backend/app/infrastructure/vector_db/repository.py:45-64`: passes through `Chroma.similarity_search_with_score`.
- `repository.py:27-31`: `Chroma(...)` is built without `collection_metadata`.
- `backend/app/infrastructure/vector_db/chroma_client.py:36`: `create_collection(name=name)` is called with no metadata and no configuration.
- `k8s/base/vectordb/chroma/entrypoint.sh:14-23`: creates only the tenant and the database, not the collection.
- No `hnsw:space` setting exists anywhere in the repo.
- `backend/app/infrastructure/vector_db/pgvector_repository.py:41-47`: `PGVectorStore.create_sync(...)` is called without `distance_strategy`.
- Library source, checked in `backend/.venv`:
  - `langchain_chroma` 0.2.4, `vectorstores.py:677-689`: the docstring says it returns "distance in float for each. Lower score represents more similarity."
  - `langchain_postgres` 0.0.16, `v2/indexes.py:29`: `DEFAULT_DISTANCE_STRATEGY = DistanceStrategy.COSINE_DISTANCE`.
  - `v2/async_vectorstore.py:769-786`: returns `row["distance"]`.
- `backend/tests/fixtures/golden_responses/chromadb_search_response.json:21,30,39,48`: real Chroma scores 0.2508, 0.2743, 0.3609 and 0.3657 with `text-embedding-ada-002`. They are ascending with the best hit first, which is the pattern of a distance.
- `backend/tests/unit/models/responses_test.py:145-149`: pins the `le=1.0` bound.
- Reproduction (scratch script with `TestClient` and dependency overrides, repository mocked):
  - A score of `0.37` returns 200.
  - A score of `1.42` returns 500 with `detail` "Error searching document: ValidationError - ... Input should be less than or equal to 1".
- The SPEC-001 working tree has one uncommitted test that works around the bound: `backend/tests/unit/api/document_scoping_test.py:27` uses identical text "to keep the L2 distance at 0, inside the response score range [0, 1]".

Score semantics are documented incorrectly in several places:

- `search_response.py:8`: "Similarity score".
- `backend/tests/fixtures/README.md:23`: "cosine similarity calculations".
- `avg_similarity_score` naming:
  - `backend/app/infrastructure/database/models.py:97`
  - `backend/app/services/persistence/interaction_service.py:35,83-88`
  - `backend/app/migrations/versions/dc37733dbbf5_initial_schema_documents_search_.py:109`
  - `docs/reference/architecture.md:159`

No doc states that the value is a distance or names the metric.

## Impact

- `POST /api/v1/documents/{id}/search` returns 500 for valid requests whenever any hit's distance is greater than 1. That is most likely with off-topic queries, with the L2 metric, or with non-normalized embeddings.
- When it succeeds, API clients get a score whose ordering is inverted relative to its documented meaning.
- The `avg_similarity_score` analytics hold mean distances.
- **Reach is limited:**
  - The Streamlit frontend never calls `/search`. It calls only `POST /documents` (`frontend/components/qa_pdf.py:19`) and `/ask` (`frontend/components/chatbot.py:15`).
  - No behave scenario exercises `/search`.
  - `/ask` does not use this field. `SourceDocument.score` is `None` (`document.py:231`).

## Severity rationale

Medium, not High. Reach decided it. The failure is confined to a direct-API endpoint that has no UI consumer and no acceptance coverage. Whether it is triggered depends on the query, the metric and the embedding model. The inverted meaning would justify High if `/search` becomes a consumer-facing contract. Raise the severity if the frontend or an external client starts using it.

## Suggested fix

Both options touch the API contract (`backend/app/models/responses/search_response.py`) and the meaning of the `search_interactions.avg_similarity_score` column. Each should be listed as a contract row in the spec.

1. **Return a real similarity in [0, 1].**
   - Configure the metric explicitly on both backends: Chroma collection space (`hnsw:space` / `configuration`) and PGVector `distance_strategy`.
   - Convert distance to relevance in the repositories, for example with LangChain's `similarity_search_with_relevance_scores`. Changing an existing Chroma collection's space requires recreating the collection and re-ingesting.
   - Caveats:
     - `langchain_chroma` picks the relevance function from collection metadata and falls back to L2 when `hnsw:space` is absent (`vectorstores.py:771-784`). This is only correct once the space is set explicitly.
     - LangChain's cosine relevance is `1 - distance`, which can be negative. Clamp it, or drop `ge=0.0`.
2. **Expose the distance honestly.**
   - Rename the field, or redefine it as `distance`.
   - Drop `le=1.0` and document the metric and the "lower is better" ordering.
   - Rename or redocument `avg_similarity_score`.
   - This is a breaking response change and needs a migration path, such as a deprecation window or an API version.

Pinning the metric explicitly is advisable in either option. Today the Chroma metric depends on server defaults.

## Follow-up

Tracked in [SPEC-001](../specs/SPEC-001-scope-retrieval-to-document.md) (T-4, T-5, AC-13 to AC-19).

- [x] Decide between similarity and distance semantics. Decided by the user on 2026-10-15:
  similarity in [0, 1], higher is better, cosine on both backends, clamped `1 − d` (option 1).
- [ ] Pin the distance metric on Chroma and PGVector
- [ ] Fix `SearchResultItem.score` bounds and description; update `responses_test.py:145-149`
- [ ] Fix `avg_similarity_score` semantics (column, `architecture.md:159`, fixtures README)
- [ ] Add a router unit test for a score greater than 1 and a behave scenario for `/search`
- [ ] Verify the effective Chroma collection space on the deployed `chromadb/chroma:1.0.0` server. Before the fix it was `l2` (checked 2026-10-15). After the fix it is SPEC-001 AC-19.
