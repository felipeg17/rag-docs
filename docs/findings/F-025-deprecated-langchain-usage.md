# F-025: Deprecated LangChain APIs; chains rebuilt per request

| Field | Value |
|---|---|
| Severity | Low |
| Category | maintenance |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | #16 (related) |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

`RetrievalQA` is deprecated; `langchain.schema` and `langchain.text_splitter` are legacy import paths. Chain, prompt and Cohere client are rebuilt on every request.

## Evidence

- `backend/app/services/rag/qa_service.py:1,69`

## Impact

Breakage on LangChain upgrades; per-request overhead.

## Suggested fix

Migrate to LCEL / `create_retrieval_chain`; build chains once.

## Follow-up

- [ ] Migrate QA chain
- [ ] Update imports
