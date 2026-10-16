# F-008: Rerank is close to a no-op and returns no sources

| Field | Value |
|---|---|
| Severity | Medium |
| Category | rag-quality |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

Retrieval k=4 (max 10) is reranked down to top_n=3, so reranking barely changes the candidate set. The rerank path returns `source_docs=[]`, so the UI gets no citations.

## Evidence

- `backend/app/core/config.py:78-79`
- `backend/app/models/requests/search_request.py:17`
- `backend/app/api/routers/v1/document.py:216`

## Impact

Pays for a Cohere call with little quality gain; no citations on the default strategy.

## Suggested fix

Retrieve ~20-30 candidates for rerank and keep top 3-5. Return the reranked docs as sources.

## Follow-up

- [ ] Separate `rerank_candidates` setting
- [ ] Return sources from rerank
