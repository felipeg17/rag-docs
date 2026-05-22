# Testing Guide

rag-docs includes unit tests and integration tests (BDD).

## Test Structure

```
backend/tests/
├── unit/                    # Unit tests
│   ├── api/                 # API endpoint tests
│   ├── services/            # Service layer tests
│   ├── repositories/        # Data access tests
│   └── fixtures/            # Shared test data
├── behave/                  # Integration/BDD tests
│   ├── features/            # Feature files (.feature)
│   └── steps/               # Step implementations
└── fixtures/
    └── golden_responses/    # Mock API responses
```

## Running Tests

### All Unit Tests

```bash
cd backend
pytest tests/unit -v
```

### Integration Tests (BDD)

Requires running backend at http://localhost:8106:

```bash
cd backend
BACKEND_URL=http://localhost:8106 behave tests/behave -v
```

Optional: Specify feature file:

```bash
behave tests/behave/features/document_ingestion.feature
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

## Integration Tests (BDD)

Feature files use Gherkin syntax:

```gherkin
# tests/behave/features/qa.feature
Feature: Question Answering
  Scenario: User asks question on ingested document
    Given a document is uploaded
    When I ask "What is the main topic?"
    Then I receive an answer
    And the answer contains source documents
```

## CI/CD Integration

Tests run automatically on:

- Every commit to a PR
- Every push to `main`
- Manual label `integration-tests` on a PR

See `.github/workflows/` for CI configuration.
