# SPEC-001: Scope retrieval to the requested document

| Field | Value |
|---|---|
| Status | Draft |
| Findings | F-001 |
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
- **Chunk metadata**: every chunk carries `titulo` and `tipo_documento` (`backend/app/services/document/text_extractor.py:43-47`).
  On PGVector they are real columns (`backend/app/infrastructure/vector_db/pgvector_client.py:13-18`).
  So a title filter needs no re-ingestion.

### Library behavior (verified against installed sources pinned in `backend/uv.lock`)

| Library | Version | Fact | Where checked |
|---|---|---|---|
| `langchain-core` | 0.3.68 | `VectorStoreRetriever._get_relevant_documents` calls `vectorstore.similarity_search(query, **search_kwargs)`, so `search_kwargs["filter"]` reaches the store | `langchain_core/vectorstores/base.py:1074-1079` |
| `langchain-chroma` | 0.2.4 | `filter` is passed to Chroma as `where=`, `where_document` as `where_document=` | `langchain_chroma/vectorstores.py:585-606,686-700` |
| `chromadb` | 1.0.12 | `validate_where` requires exactly one top-level key. It rejects multi-key dicts (`{"a":1,"b":2}`), `{}`, and `$and`/`$or` with fewer than 2 elements. Nested `$and`/`$or` is accepted. | `chromadb/api/types.py:731-763` + executed |
| `langchain-postgres` | 0.0.16 | `PGVectorStore` (v2) accepts `$and`/`$or`/`$not`, multi-key dicts (implicit AND) and single-element `$and`. A field name is emitted raw as a SQL column, so it must be a valid identifier (`tipo-documento` raises `ValueError`); a non-column key yields a SQL error. An empty or absent filter means no `WHERE`. | `langchain_postgres/v2/async_vectorstore.py:606-618,1041-1240` + executed |
| `langchain-postgres` | 0.0.16 | `where_document` is not referenced anywhere in the package. It falls into `**kwargs` and is silently ignored. | `grep -rn where_document langchain_postgres/` → no match |

"Executed" means the filter shapes were run through `chromadb.api.types.validate_where` and
`AsyncPGVectorStore._create_filter_clause` in the backend venv. One filter shape is valid on both
backends:

```python
{"titulo": {"$eq": "<title>"}}                                       # one clause
{"$and": [{"titulo": {"$eq": "<title>"}}, {"tipo_documento": {"$eq": "<type>"}}, ...]}  # 2+ clauses
```

## Goals

- Every retrieval behind `/search` and `/ask` (both strategies) returns only chunks of the
  requested document, on both Chroma and PGVector.
- A client-supplied `metadata_filter` can only narrow results within the document, never widen
  them. It is honored on `/ask` as well as `/search`.

## Non-goals

- Changing document identity (title → UUID or content hash), title uniqueness, or storing a
  `document_id` in chunk metadata ([F-002](../findings/F-002-inconsistent-document-identity.md), #20;
  [F-023](../findings/F-023-mislabelled-path-params.md)). This spec scopes by `titulo`, the same key
  the existing 404 check uses (`document.py:127,202`).
- Fixing the `document_type` value mismatch or making it a request input
  ([F-024](../findings/F-024-unwritten-logged-fields.md), #15), beyond what OQ-1 decides.
- Moving or removing `where_document` ([F-012](../findings/F-012-chroma-only-where-document.md)).
  Its current behavior is kept as is: applied on Chroma, ignored on PGVector.
- New error handling or status codes for malformed filters ([F-007](../findings/F-007-error-handling-leaks-internals.md)),
  unless OQ-2 decides otherwise.
- Rerank sources ([F-008](../findings/F-008-rerank-near-noop.md)) and rerank context formatting
  ([F-004](../findings/F-004-rerank-context-not-formatted.md)).
- `backend/tests/fixtures/generate_golden_responses.py`, which filters on `tipo-documento`
  (`:127,180,257,322`). That key does not exist and is not a valid PGVector identifier.
- Frontend changes. `frontend/components/chatbot.py:15-21` already sends the title in the path and
  `metadata_filter: {}`. Its URL encoding is [F-028](../findings/F-028-frontend-requests.md).

## Requirements

- **REQ-1**: When `/api/v1/documents/{document_id}/search` is called, the system shall return only
  chunks whose `titulo` equals `{document_id}`.
- **REQ-2**: When `/api/v1/documents/{document_id}/ask` is called with `strategy` `standard` or
  `rerank`, the system shall retrieve only chunks whose `titulo` equals `{document_id}`. This
  includes the `source_documents` returned for `standard`.
- **REQ-3**: When a request carries a non-empty `metadata_filter`, the system shall apply it in
  conjunction (AND) with the document scope on both endpoints. It shall never replace or widen the
  scope. An empty or absent `metadata_filter` adds no condition.
- **REQ-4**: The `tipo_documento` condition currently applied (`"documento-pdf"`) shall remain part
  of the scope (pending OQ-1).
- **REQ-5**: REQ-1 to REQ-3 shall hold for both vector backends (`VECTOR_DB_TYPE` Chroma and
  PGVector), using one filter that is valid in both grammars.
- **REQ-6**: The `where_document` behavior of each backend shall not change.

## Contracts

| Contract | Before | After | Breaking? |
|---|---|---|---|
| API models (`backend/app/models/`) | `DocumentSearchRequest.metadata_filter` and `QuestionRequest.metadata_filter` are `dict`, default `{}`, "Optional metadata filters" (`search_request.py:9,18`). `/search`: replaces the type filter. `/ask`: ignored. | Schema unchanged; `Field` description updated to state it is AND-ed with the document scope. `/search` and `/ask`: AND-ed with the document scope. | Behavioral only. In-repo callers send `{}` (`frontend/components/chatbot.py:21`, `backend/tests/behave/steps/document_qa_steps.py:21`, `document_qa_rerank_steps.py:16`, `document_processing_steps.py:106`) and are unaffected. |
| HTTP routes / status codes | — | None | No |
| `Settings` ↔ configmaps ↔ `backend.env.template` | — | None | No |
| DB schema / Alembic migration | — | None | No |
| Vector DB metadata / collection / table | — | None. Reads the existing `titulo` key (`text_extractor.py:44`, PG column `pgvector_client.py:14`); no re-ingestion; vector dimension untouched. | No |
| Prompts (`backend/app/prompts/`) | — | None | No |
| CI jobs / gates | — | None | No |
| Internal service signatures (backend-only) | `QAService.answer_question(query, document_type, k_results=None, custom_prompt=None)`; `RerankService.answer_question(query, document_type, k_results=None, rerank_top_n=None, custom_prompt=None)` | Both add keyword-only `document_title: str` (required) and `metadata_filter: dict \| None = None` | Internal; only caller is `document.py` |

## Design

**Filter builder (new, one place).** Add a pure function in
`backend/app/infrastructure/vector_db/filters.py`:

```python
def build_document_filter(
    document_title: str,
    document_type: str | None = None,
    metadata_filter: dict | None = None,
) -> dict: ...
```

1. Clauses start as `[{"titulo": {"$eq": document_title}}]`. If `document_type` is given, append
   `{"tipo_documento": {"$eq": document_type}}`.
2. If `metadata_filter` is non-empty:
   - a dict with one key (a field or `$and`/`$or`/`$not`) is appended as one clause;
   - a dict with several field keys is split into one clause per key. Chroma rejects multi-key
     dicts; PGVector treats them as AND, so splitting keeps the meaning on both.
3. Return the single clause itself when there is one, or `{"$and": clauses}` when there are two or
   more. Chroma rejects a one-element `$and`.

The title clause is always a top-level conjunct, so no client filter can widen the scope. A client
filter of `{"titulo": "other"}` yields an empty result. The output shape is valid on both backends
(verified above), so the repositories need no backend-specific translation.

**Services.**
- `QAService.answer_question` and `RerankService.answer_question` gain keyword-only
  `document_title` and `metadata_filter`.
- They set `search_kwargs["filter"] = build_document_filter(document_title, document_type, metadata_filter)`
  in place of the type-only filter at `qa_service.py:59` and `rerank_service.py:69`.
- `k` and `where_document` stay as they are (REQ-6).

**Router.**
- `ask_question` passes `document_title=document_id` and `metadata_filter=request.metadata_filter`
  to whichever service it calls.
- `search_document` passes
  `metadata_filter=build_document_filter(document_id, "documento-pdf", request.metadata_filter)` to
  `vdb_repo.similarity_search_with_score`. `"documento-pdf"` is the value the repositories default
  to today (`repository.py:54`, `pgvector_repository.py:68`), so behavior is unchanged apart from
  the added title clause.

**Repositories.**
- In both `similarity_search_with_score`, replace `metadata_filter or {...}` with
  `{...} if metadata_filter is None else metadata_filter`.
- A caller-supplied filter is never silently replaced; the router always supplies a non-empty one.
- Nothing else in the repositories changes.

**Alternatives considered.**
- *Per-backend filter translation inside each repository.* Rejected: one shape is already valid on
  both backends, so translation adds code with no benefit. F-012 can still push `where_document`
  into the repositories later.
- *`RetrievalQA`/LCEL retriever wrapper that post-filters by title.* Rejected: post-filtering after
  top-k returns fewer than k chunks and still ranks against foreign documents.
- *Scope by Postgres document UUID.* Rejected here: chunks carry no `document_id` and titles are not
  unique (F-002). `build_document_filter` is the single seam to change once F-002 lands.

## Acceptance criteria

| ID | Given / When / Then | Verified by |
|---|---|---|
| AC-1 | Given these inputs to `build_document_filter`: (a) title only; (b) title + type; (c) title + type + single-key `metadata_filter`; (d) title + multi-key `metadata_filter`; (e) title + `metadata_filter` that is a `$and` or `$or` expression. Then for each, the output contains `{"titulo": {"$eq": <title>}}` as the whole filter or as a direct element of the top-level `$and`. It passes `chromadb.api.types.validate_where`. It passes `AsyncPGVectorStore._create_filter_clause` (instance via `object.__new__`) without raising. | `backend/tests/unit/infrastructure/vector_db_filters_test.py` |
| AC-2 | Given title only and `metadata_filter` `None` or `{}`, the output is exactly `{"titulo": {"$eq": <title>}}`. There is no `$and` wrapper and no extra clause. | `backend/tests/unit/infrastructure/vector_db_filters_test.py` |
| AC-3 | Given `metadata_filter={"titulo": "other-doc"}` for title `doc-a`, the output still has `{"titulo": {"$eq": "doc-a"}}` as a top-level conjunct. | `backend/tests/unit/infrastructure/vector_db_filters_test.py` |
| AC-4 | When `QAService.answer_question(..., document_title="doc-a")` runs, `as_retriever` receives `search_kwargs["filter"] == build_document_filter("doc-a", <document_type>, <metadata_filter>)`. `search_kwargs["where_document"] == {"$contains": " "}` is unchanged. | `backend/tests/unit/services/rag/qa_service_test.py` |
| AC-5 | Same as AC-4 for `RerankService.answer_question`. | `backend/tests/unit/services/rag/rerank_service_test.py` |
| AC-6 | When `POST /api/v1/documents/doc-a/ask` is called with `strategy` `standard`, and again with `rerank`, and `metadata_filter={"pagina": 1}`, the called service receives `document_title="doc-a"` and `metadata_filter={"pagina": 1}`. | `backend/tests/unit/api/document_router_test.py` |
| AC-7 | When `POST /api/v1/documents/doc-a/search` is called with `metadata_filter={}`, `similarity_search_with_score` receives a `metadata_filter` equal to `build_document_filter("doc-a", "documento-pdf", {})`. | `backend/tests/unit/api/document_router_test.py` |
| AC-8 | Given a caller-supplied non-`None` filter, both `VectorDBRepository` and `PGVectorDBRepository` `similarity_search_with_score` forward it unchanged as `filter=`. With `None`, both use `{"tipo_documento": "documento-pdf"}`. | `backend/tests/unit/infrastructure/vector_db_repository_test.py`, `backend/tests/unit/infrastructure/pgvector_repository_test.py` (new) |
| AC-9 | Given a deployed stack with two distinct PDFs ingested under different titles, when `/search` is called on one title, then at least one result is returned and every result has `metadata.titulo` equal to that title. | `behave backend/tests/behave/document_scoping.feature` (deployed stack) |
| AC-10 | Given the same two documents, when `/ask` (`strategy=standard`) is called on one title, then every `source_documents[].metadata.titulo` equals that title. | `behave backend/tests/behave/document_scoping.feature` (deployed stack; live LLM) |
| AC-11 | Gates show no new errors beyond the baseline in `.claude/CLAUDE.md`. | `cd backend && uv run pytest tests/unit` → all pass (≥ 130 + new); `uv run ruff check app tests` → only the two baseline errors; `uv run ruff format --check app` and `uv run mypy app` → clean |

## Tasks

| ID | Task | Agent | Depends on | Files | Status |
|---|---|---|---|---|---|
| T-1 | Add `build_document_filter`. Use it in `QAService`, `RerankService` and the `/search` + `/ask` handlers. Pass `document_title`/`metadata_filter` through. Replace `or` with an `is None` default in both repositories. Update the `metadata_filter` `Field` descriptions. Add or adjust unit tests for AC-1 to AC-8. | backend-agent | — | `backend/app/infrastructure/vector_db/filters.py` (new), `backend/app/infrastructure/vector_db/repository.py`, `backend/app/infrastructure/vector_db/pgvector_repository.py`, `backend/app/services/rag/qa_service.py`, `backend/app/services/rag/rerank_service.py`, `backend/app/api/routers/v1/document.py`, `backend/app/models/requests/search_request.py`, `backend/tests/unit/infrastructure/vector_db_filters_test.py` (new), `backend/tests/unit/infrastructure/pgvector_repository_test.py` (new), `backend/tests/unit/infrastructure/vector_db_repository_test.py`, `backend/tests/unit/services/rag/qa_service_test.py`, `backend/tests/unit/services/rag/rerank_service_test.py`, `backend/tests/unit/api/document_router_test.py` | Todo |
| T-2 | Add a behave feature for AC-9 and AC-10 with a second, content-distinct PDF fixture. Only `ros-intro.pdf` exists today. Do not reuse the same PDF under a second title: that path depends on F-002's dedup behavior. | qa-agent | T-1 | `backend/tests/behave/document_scoping.feature` (new), `backend/tests/behave/steps/document_scoping_steps.py` (new), `backend/tests/behave/data/<second>.pdf` (new) | Todo |
| T-3 | Update `docs/reference/architecture.md` (§ Vector Database Storage, § API Endpoints) to state that retrieval is scoped by `titulo` and that `metadata_filter` is AND-ed with it. | architect | T-1 | `docs/reference/architecture.md` | Todo |

No frontend, k8s or ci task: no API schema, setting, manifest or workflow changes. `docs/guides/`
and `docs/development/` do not describe `metadata_filter` or retrieval filtering (checked with
`grep -rn metadata_filter docs`).

## Open questions

- [ ] **OQ-1: Keep the `tipo_documento` clause in the scope?**
  - Today ingestion stores the caller's `document_type` (`document.py:51,66`, default
    `"documento-pdf"`), but `/ask` and `/search` always filter on `"documento-pdf"` (`document.py:213,222`;
    `repository.py:54`). A document ingested with any other type retrieves nothing, and still won't
    after this spec if the clause stays.
  - Once retrieval is title-scoped, the type clause adds no isolation, only that failure mode (F-024).
  - Options:
    - **(a)** keep it, as REQ-4 does now: smallest behavior change, and the type is left to F-024/#15;
    - **(b)** drop it from the scope: retrieval filters on `titulo` (plus any client `metadata_filter`) only.
  - **Recommendation: (b).** If chosen, REQ-4 becomes "shall not filter on `tipo_documento`". The
    `document_type` arguments become unused in the services and router, and should be removed in
    T-1. AC-4, AC-5 and AC-7 expect `build_document_filter(title, None, ...)`.
- [ ] **OQ-2: Validate client `metadata_filter` keys?**
  - On PGVector, a key that is not a metadata column (`titulo`, `tipo_documento`, `pagina`, `fuente`;
    `pgvector_client.py:13-18`) or not an identifier raises inside the store. That surfaces as a 500
    (`document.py:170-178,259-267`). Chroma's behavior for an unknown key was not verified
    (assumed: no match, empty result).
  - This already happens on `/search`. Honoring the filter on `/ask` (REQ-3) newly exposes it there.
  - Options:
    - **(a)** pass the filter through and accept the 500 until F-007;
    - **(b)** validate in the request models (recursive walk; allow only those 4 field keys plus
      `$and`/`$or`/`$not` and the operators both backends support). This returns 422, which adds a
      status-code contract and AC.
    - **(c)** keep ignoring `metadata_filter` on `/ask`. This drops the second half of REQ-3.
  - **Recommendation: (a)**, to keep this spec to F-001. All in-repo callers send `{}`.
- [ ] **OQ-3: Ship title scoping now, or wait for F-002 (#20) to settle the document identity?**
  - Scoping by `titulo` matches the existing existence check and needs no migration.
  - Under F-002, two different PDFs with the same title cannot both be in the vector store: the
    second is skipped (`document.py:57-60`). So title scoping is correct for what is stored.
  - **Recommendation: ship now.** `build_document_filter` is the single seam F-002 would change.

## Verification

Filled by `qa-agent` during `/spec verify`.

| AC | Result | Evidence |
|---|---|---|
| AC-1 | | |
| AC-2 | | |
| AC-3 | | |
| AC-4 | | |
| AC-5 | | |
| AC-6 | | |
| AC-7 | | |
| AC-8 | | |
| AC-9 | | |
| AC-10 | | |
| AC-11 | | |

## Changelog

- 2026-10-15: Draft created.
