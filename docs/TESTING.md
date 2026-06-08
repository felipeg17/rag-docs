# Testing Guide

rag-docs includes unit tests and integration tests (BDD).

## Test Structure

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

## Running Tests

### All Unit Tests

```bash
cd backend
pytest tests/unit -v
```

### Integration Tests (BDD)

Feature files use Gherkin syntax and live in `backend/tests/behave/features/`:

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
uv run behave -v backend/tests/behave/features/document_ingestion.feature
```

### Linting and Type Checking

```bash
cd backend

# Lint
ruff check app

# Format
ruff format app

# Type check
mypy app
```

## CI/CD Integration

Tests run automatically on:

- Every commit to a PR
- Every push to `main`
- Manual label `integration-tests` on a PR

See `.github/workflows/` for CI configuration.
