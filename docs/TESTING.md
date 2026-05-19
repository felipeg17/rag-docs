# Testing Guide

rag-docs includes unit tests and integration tests (BDD). This guide covers running, writing, and maintaining tests.

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

### Specific Test Module

```bash
pytest tests/unit/services/rag/qa_service_test.py -v
```

### Single Test

```bash
pytest tests/unit/services/rag/qa_service_test.py::TestQAService::test_answer_generation -v
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

### All Checks (linting, types, unit tests)

```bash
cd backend
ruff check app && mypy app && pytest tests/unit -v
```

## Unit Test Examples

### Testing a Service

```python
# tests/unit/services/rag/qa_service_test.py
import pytest
from unittest.mock import MagicMock
from app.services.rag.qa_service import QAService

@pytest.fixture
def mock_vector_db():
    return MagicMock()

@pytest.fixture
def qa_service(mock_vector_db):
    return QAService(vector_db=mock_vector_db)

def test_answer_generation(qa_service, mock_vector_db):
    mock_vector_db.retrieve.return_value = ["relevant chunk 1", "relevant chunk 2"]
    
    result = qa_service.answer("What is RAG?", document_id="test-doc")
    
    assert result.answer is not None
    mock_vector_db.retrieve.assert_called_once()
```

### Testing an API Endpoint

```python
# tests/unit/api/documents_test.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_search_endpoint():
    response = client.post(
        "/api/v1/documents/test-doc/search",
        json={"query": "what is RAG?"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
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

Step implementations:

```python
# tests/behave/steps/qa_steps.py
from behave import given, when, then

@given('a document is uploaded')
def step_upload_document(context):
    # Call backend API to upload
    context.doc_id = "test-doc"

@when('I ask "{question}"')
def step_ask_question(context, question):
    # Call ask endpoint
    context.response = requests.post(...)

@then('I receive an answer')
def step_check_answer(context):
    assert context.response.status_code == 200
    assert "answer" in context.response.json()
```

## Golden Response Fixtures

Mock API responses are stored in `backend/tests/fixtures/golden_responses/` for consistent unit test behavior without hitting real APIs.

To update fixtures (e.g., after LLM output format changes):

```bash
# Regenerate fixtures (requires live APIs)
cd backend
python tests/fixtures/generate_golden_responses.py
```

## Coverage

Check test coverage:

```bash
cd backend
pytest --cov=app tests/unit
```

Generate HTML report:

```bash
pytest --cov=app --cov-report=html tests/unit
# Open htmlcov/index.html
```

## CI/CD Integration

Tests run automatically on:
- Every commit to a PR
- Every push to `main`
- Manual label `integration-tests` on a PR

See `.github/workflows/` for CI configuration.

## Writing New Tests

### Naming Conventions

- Test files: `*_test.py`
- Test classes: `Test<ComponentName>`
- Test methods: `test_<behavior_being_tested>`

### Best Practices

1. **Isolation**: Mock external dependencies (LLMs, databases)
2. **Clarity**: One assertion per test (or tightly related assertions)
3. **Fixtures**: Use pytest fixtures for setup/teardown
4. **BDD**: Use integration tests for user-facing workflows
5. **Golden responses**: Use fixtures for API calls, not mocks

### Example: Testing a New Service

```python
# app/services/new_service.py
class NewService:
    def process(self, input_data: str) -> str:
        return f"Processed: {input_data}"

# tests/unit/services/test_new_service.py
import pytest
from app.services.new_service import NewService

class TestNewService:
    @pytest.fixture
    def service(self):
        return NewService()
    
    def test_process_valid_input(self, service):
        result = service.process("hello")
        assert result == "Processed: hello"
    
    def test_process_empty_input(self, service):
        result = service.process("")
        assert result == "Processed: "
```

## Debugging Tests

### Verbose Output

```bash
pytest -vv tests/unit/services/rag/qa_service_test.py
```

### Print Statements

Use `print()` or Python debugger:

```bash
pytest -s tests/unit/services/rag/qa_service_test.py  # Show print output
pytest --pdb tests/unit/services/rag/qa_service_test.py  # Drop to debugger on failure
```

### Specific Test Selection

```bash
pytest -k "test_answer" tests/unit/  # Run tests matching pattern
```

## Troubleshooting

### Import Errors

Ensure you're running from `backend/` directory and environment is activated.

### Integration Tests Fail: Connection Refused

Start backend before running integration tests:

```bash
# Terminal 1
cd backend
uvicorn main:app --reload

# Terminal 2
cd backend
BACKEND_URL=http://localhost:8106 behave tests/behave -v
```

### Fixtures Not Found

Golden responses are auto-loaded if placed in `backend/tests/fixtures/golden_responses/`. Verify file structure matches module path.
