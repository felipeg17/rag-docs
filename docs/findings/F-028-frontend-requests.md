# F-028: Frontend HTTP calls: no URL encoding, timeout or error handling

| Field | Value |
|---|---|
| Severity | Low |
| Category | frontend |
| Status | Open |
| Verification | Reported — found by code reading, not reproduced |
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

- [ ] Encode + timeout + error handling
- [ ] Strategy/k selector
