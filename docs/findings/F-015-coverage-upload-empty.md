# F-015: Codecov upload has no coverage report

| Field | Value |
|---|---|
| Severity | Medium |
| Category | ci |
| Status | Open |
| Verification | Confirmed — manually checked against source |
| Tracking issue | — |
| Found | 2026-10-15 — [repo audit](README.md#audits) |

## Problem

pytest runs without `--cov` and pytest-cov is not a dependency, so `coverage.xml` is never produced.

## Evidence

- `.github/workflows/submission-check.yml:162-171`
- `backend/pyproject.toml`

## Impact

Coverage is not tracked despite the CI step.

## Suggested fix

Add pytest-cov to dev deps; run `pytest --cov=app --cov-report=xml`.

## Follow-up

- [ ] Add pytest-cov
- [ ] Update workflow
