# F-028: Frontend HTTP calls: no URL encoding, timeout or error handling

| Field | Value |
|---|---|
| Severity | Low |
| Category | frontend |
| Status | Fixed (SPEC-002) |
| Verification | Confirmed — 2026-10-16, architect, `dev` @ `1fbb820`: re-read `frontend/components/chatbot.py:15` (title interpolated unencoded), `:19-20` (strategy `rerank`, k=4 hard-coded), `:26` and `qa_pdf.py:29` (`requests.post` without timeout or exception handling), `chatbot.py:33`/`qa_pdf.py:36` (raw `response.text` shown). Note: encoding alone cannot make titles containing `/` reachable (uvicorn unquotes `%2F`, Starlette `str` matches `[^/]+`). See [SPEC-002](../specs/SPEC-002-web-frontend.md) |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

Titles go into the URL unencoded (`/`, `?`, `#`, spaces break routing). `requests.post` has no timeout or `RequestException` handling. Strategy hardcoded to `rerank`, k=4.

## Evidence

- `frontend/components/chatbot.py:15,26`
- `frontend/components/qa_pdf.py:29`

## Impact

Broken requests for some titles; UI hangs on backend stalls.

## Suggested fix

`urllib.parse.quote(title, safe="")`, timeouts, error messages, strategy selector.

## Follow-up

- [x] Encode + timeout + error handling
- [x] Strategy selector ([SPEC-002](../specs/SPEC-002-web-frontend.md), "Estándar / Rerank" control)
- `k` selector: out of scope by user decision (2026-10-16, SPEC-002 open question 7); the UI always sends `k_results: 4`, the backend default
