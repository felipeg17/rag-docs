# F-029: Frontend UX and security settings

| Field | Value |
|---|---|
| Severity | Low |
| Category | frontend |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

Responses dumped as key/value pairs, no sources shown, no chat history, "Chabot" typo. Upload doesn't validate a non-empty title. CORS and XSRF protection disabled. `packages=["front"]` refers to a non-existent package.

## Evidence

- `frontend/components/chatbot.py:8`
- `frontend/Dockerfile:31-37`
- `frontend/pyproject.toml:23`

## Impact

Poor UX; weaker protection if exposed publicly.

## Suggested fix

Chat history with `st.chat_message`, render sources, validate input, re-enable XSRF.

## Follow-up

- [ ] Chat UX
- [ ] Input validation
- [ ] Review CORS/XSRF flags
