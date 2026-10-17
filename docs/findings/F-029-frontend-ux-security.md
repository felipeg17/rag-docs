# F-029: Frontend UX and security settings

| Field | Value |
|---|---|
| Severity | Low |
| Category | frontend |
| Status | Fixed (SPEC-002) |
| Verification | Confirmed — 2026-10-16, architect, `dev` @ `1fbb820`: re-read `frontend/components/chatbot.py:8` ("Chabot"), `:30-31` and `qa_pdf.py:31-36` (responses dumped as key/value lines, sources not rendered), `qa_pdf.py:14` (title not validated; backend `DocumentIngestRequest.title` has no `min_length`, `document_request.py:8`), `frontend/Dockerfile:31-37` (`enableCORS = false`, `enableXsrfProtection = false`, written under `/root`, no `USER`), `frontend/pyproject.toml:23` (`packages = ["front"]`, no such package). No chat history (single request/response per click). See [SPEC-002](../specs/SPEC-002-web-frontend.md) |
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

- [x] Chat UX
- [x] Input validation
- [x] Review CORS/XSRF flags
