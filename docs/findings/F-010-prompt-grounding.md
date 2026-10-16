# F-010: Prompt lacks grounding fallback; prompt load failures are silent

| Field | Value |
|---|---|
| Severity | Medium |
| Category | rag-quality |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

No "say you don't know if the context lacks the answer" instruction and no citation instruction. The prompt is loaded at class definition time and `load_prompt` returns `""` on failure, producing an empty template instead of failing at startup.

## Evidence

- `backend/app/prompts/prompts.yaml:1-17`
- `backend/app/services/rag/qa_service.py:16`
- `backend/app/utils/load_prompt.py:19-24`

## Impact

Hallucinated answers; a broken prompt file goes unnoticed.

## Suggested fix

Add grounding and citation instructions; raise on prompt load failure.

## Follow-up

- [ ] Update prompts.yaml
- [ ] Raise in load_prompt + test
