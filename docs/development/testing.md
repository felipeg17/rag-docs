# Testing Guide

rag-docs includes backend unit tests, backend integration tests (BDD) and frontend unit tests.

## Test Structure

### Backend

```
backend/tests/
├── unit/
│   ├── api/                 # Route handler tests
│   ├── infrastructure/      # Client and repository tests
│   ├── models/              # Request/response model tests
│   └── services/            # Service layer tests
│       ├── document/
│       ├── ingest/
│       ├── persistence/
│       └── rag/
├── behave/                  # Integration/BDD tests
│   ├── features/            # Gherkin feature files
│   ├── steps/               # Step implementations
│   └── data/                # Test data files
└── fixtures/
    ├── data/                # Sample PDF files
    ├── golden_responses/    # Saved API responses for mocking
    └── generate_golden_responses.py
```

`backend/tests/unit/openapi_snapshot_test.py` fails when `backend/openapi.json` differs from what the
FastAPI app produces (see [contributing.md](contributing.md#api-types)).

### Frontend

Unit tests (vitest + Testing Library, jsdom) sit next to the code they cover as `*.test.ts(x)`:

```
frontend/src/
├── api/                     # client.test.ts, errors.test.ts
├── components/              # one <component>.test.tsx per component
├── app.test.tsx             # views, routing, session state
├── validation.test.ts
└── test/                    # shared test helpers
```

## Running Tests

### Backend Unit Tests

```bash
cd backend
pytest tests/unit -v
```

### Frontend Unit Tests

Requires Node 24 and npm.

```bash
cd frontend
npm ci
npm test
```

### Integration Tests (BDD)

Feature files use Gherkin syntax and live in `backend/tests/behave/`:

```gherkin
Feature: Question Answering
  Scenario: User asks question on ingested document
    Given a document is uploaded
    When I ask "What is the main topic?"
    Then I receive an answer
    And the answer contains source documents
```

Run all integration tests:

```bash
uv run behave -v backend/tests/behave/
```

Run a single feature file:

```bash
uv run behave -v backend/tests/behave/document_ingestion.feature
```

### Linting and Type Checking

Backend:

```bash
cd backend

# Lint
ruff check app

# Format
ruff format app

# Type check
mypy app
```

Frontend (Biome is the only linter and formatter; rules in `frontend/biome.jsonc`):

```bash
cd frontend
npm run check:api   # src/api/openapi_gen.ts matches ../backend/openapi.json
npm run lint        # biome check --error-on-warnings . (lint + format + import order)
npm run format      # biome check --write . (apply fixes)
npm run typecheck   # tsc -b
npm test            # vitest run
npm run build       # tsc -b && vite build
```

## CI/CD Integration

Tests run automatically on:

- Every commit to a PR
- Every push to `main`
- Manual label `integration-tests` on a PR

`submission-check.yml` runs per component, only for the paths a PR touches:

- Backend: `ruff format --check`, `mypy app/`, `pytest tests/unit/`.
- Frontend (Node 24, npm cache keyed on `frontend/package-lock.json`): `npm ci`, `npm run check:api`,
  `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`. A backend-only PR that changes
  `backend/openapi.json` also runs this job.

See `.github/workflows/` for CI configuration.
