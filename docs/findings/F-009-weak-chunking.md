# F-009: Chunking strategy is weak

| Field | Value |
|---|---|
| Severity | Medium |
| Category | rag-quality |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

800 characters with 50 overlap (~6%), measured in characters not tokens. Splitting is per page, so chunks never cross page breaks. `chunk_size or default` makes 0 impossible.

## Evidence

- `backend/app/services/document/text_splitter.py:45-52`
- `backend/app/core/config.py:76-77`

## Impact

Context split mid-thought; poor recall on content spanning pages.

## Suggested fix

10-20% overlap, `RecursiveCharacterTextSplitter.from_tiktoken_encoder` (tiktoken is already a dependency), split the joined document while keeping page metadata, use `is None` checks.

## Follow-up

- [ ] Token-based splitter
- [ ] Evaluate retrieval quality before/after
