# F-004: Rerank chain injects raw `list[Document]` into the prompt

| Field | Value |
|---|---|
| Severity | High |
| Category | rag-quality |
| Status | Open |
| Verification | Confirmed — manually checked against source |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

`{"context": compression_retriever}` has no formatting step, so the prompt receives the Python repr of the documents (metadata included). The standard path uses a stuff chain that joins `page_content`, so the two strategies are not comparable.

## Evidence

- `backend/app/services/rag/rerank_service.py:91-95`

## Impact

Noisy context, wasted tokens, lower answer quality on the strategy the frontend uses by default.

## Suggested fix

`compression_retriever | (lambda docs: "\n\n".join(d.page_content for d in docs))`.

## Follow-up

- [ ] Add formatting step
- [ ] Test that the rendered prompt contains only page content
