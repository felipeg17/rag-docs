# RAG-Docs Unit Testing Infrastructure

This directory contains unit tests for the RAG-docs application following a **Golden Fixtures Pattern** for deterministic testing.

## 📁 Directory Structure

```
tests/
├── __init__.py
├── README.md                      # This file
├── unit/                          # Unit tests (fast, isolated)
│   ├── __init__.py
│   ├── test_models.py            # ✅ Pydantic model tests
│   ├── test_handlers.py          # TODO: Handler layer tests
│   ├── test_process_document.py  # TODO: ProcessDocument service tests
│   ├── test_api_endpoints.py     # TODO: API endpoint tests
│   └── test_pdf_processing.py    # TODO: PDF processing tests
└── fixtures/
    ├── conftest.py               # ✅ Pytest fixtures (mocks, golden responses)
    └── golden_responses/         # ✅ Pre-recorded API responses
        ├── README.md
        ├── embedding_response.json
        ├── chromadb_search_response.json
        └── cohere_rerank_response.json
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install pytest and pytest-mock
pip install pytest pytest-mock

# Or with uv
uv pip install pytest pytest-mock
```

### 2. Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run only unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_models.py -v

# Run tests matching a pattern
pytest -k "test_valid" -v
```

### 3. Check Test Coverage

```bash
# Install coverage tool
pip install pytest-cov

# Run tests with coverage
pytest --cov=app --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

## 🎯 Testing Strategy

### Golden Fixtures Pattern

We use **golden responses** for deterministic testing of external services:

1. **Record Once**: Capture real API responses from OpenAI, ChromaDB, Cohere
2. **Store as JSON**: Save responses in `fixtures/golden_responses/`
3. **Replay in Tests**: Load golden responses instead of calling real APIs

**Benefits**:
- ✅ Fast tests (no API calls)
- ✅ Deterministic (same input → same output)
- ✅ Offline testing (no internet required)
- ✅ No API costs during testing

### Mocking Strategy

| Service | Strategy | Reason |
|---------|----------|--------|
| OpenAI LLM | **Mock** | Non-deterministic responses |
| OpenAI Embeddings | **Golden Fixtures** | Deterministic vectors |
| ChromaDB | **Golden Fixtures** | Deterministic search results |
| Cohere Reranking | **Golden Fixtures** | Deterministic rankings |
| PyMuPDF | **Real/Simple PDFs** | Fast text extraction |

## 📝 Available Fixtures

All fixtures are defined in `tests/fixtures/conftest.py`.

### Path Fixtures
```python
def test_example(test_documents_dir, golden_responses_dir):
    pdf_path = test_documents_dir / "sample.pdf"
    golden_path = golden_responses_dir / "response.json"
```

### Document Fixtures
```python
def test_example(sample_pdf_bytes, sample_pdf_base64):
    # Use pre-loaded PDF bytes or base64 string
    assert len(sample_pdf_bytes) > 0
    assert isinstance(sample_pdf_base64, str)
```

### Request Fixtures
```python
def test_example(sample_process_document_request, sample_search_request):
    # Use pre-configured request dictionaries
    request = ProcessDocumentRequest(**sample_process_document_request)
```

### Mock Service Fixtures
```python
def test_example(
    mock_openai_llm,
    mock_openai_embeddings,
    mock_chroma_client,
    mock_chroma_vdb,
    mock_cohere_reranker,
):
    # Use mocked external services
    response = mock_openai_llm.invoke("test query")
```

### Composite Fixture
```python
def test_example(mock_process_document_services):
    # Get all mocked services at once
    llm = mock_process_document_services["llm"]
    embeddings = mock_process_document_services["embeddings"]
    chroma_client = mock_process_document_services["chroma_client"]
    chroma_vdb = mock_process_document_services["chroma_vdb"]
```

## 🧪 Writing New Tests

### Example: Testing a Handler

```python
# tests/unit/test_handlers.py
import pytest
from app.procesar_documento.services.process_document_handlers import ProcessDocumentHandler
from app.procesar_documento.models.process_document_request import ProcessDocumentRequest


def test_process_document_handler(
    sample_pdf_base64,
    mock_process_document_services,
    mocker,
):
    """Test ProcessDocumentHandler with mocked services."""
    # Arrange: Create request
    request = ProcessDocumentRequest(
        title="test_doc",
        document_chain=sample_pdf_base64,
    )

    # Arrange: Mock ProcessDocument class
    mock_process_doc = mocker.patch(
        "app.procesar_documento.services.process_document_handlers.ProcessDocument"
    )
    mock_instance = mock_process_doc.return_value
    mock_instance.process_document.return_value = True

    # Act: Execute handler
    handler = ProcessDocumentHandler(query_id="test-123", input_data=request)
    result = handler.process_document()

    # Assert: Verify behavior
    assert result is True
    mock_instance.load_services.assert_called_once()
    mock_instance.load_document.assert_called_once()
    mock_instance.process_document.assert_called_once()
```

## 🔧 Updating Golden Responses

When external service responses change, regenerate golden responses:

### Option 1: Manual Recording

1. Run your application with real services
2. Copy API responses
3. Update JSON files in `fixtures/golden_responses/`

### Option 2: Golden Response Generator Script (TODO)

```bash
# Future script to automate golden response generation
python tests/fixtures/generate_golden_responses.py
```

**Prerequisites for generation**:
- ChromaDB running
- Valid API keys in `.env`
- At least one document ingested

## 📊 Test Markers

Use markers to categorize and run specific test types:

```python
@pytest.mark.unit
def test_fast_unit_test():
    pass

@pytest.mark.slow
def test_slow_operation():
    pass

@pytest.mark.requires_chromadb
def test_with_chromadb():
    pass
```

Run specific markers:
```bash
# Run only unit tests
pytest -m unit

# Run all except slow tests
pytest -m "not slow"

# Run tests requiring ChromaDB
pytest -m requires_chromadb
```

## 🐛 Debugging Tests

```bash
# Stop on first failure
pytest -x

# Show local variables on failure
pytest --showlocals

# Drop into debugger on failure
pytest --pdb

# Run specific test with verbose output
pytest tests/unit/test_models.py::TestProcessDocumentRequest::test_valid_request_with_all_fields -vv
```

## ✅ Current Test Coverage

### Completed ✅
- **Pydantic Models** (`test_models.py`)
  - ProcessDocumentRequest validation
  - SearchVectorDataBaseRequest validation
  - Default values and optional fields
  - Serialization/deserialization

### TODO 📝
- **Handler Layer** (`test_handlers.py`)
  - ProcessDocumentHandler
  - SearchVectorDataBaseHandler
  - QueryQAChainHandler
  - QueryRerankChainHandler

- **Service Layer** (`test_process_document.py`)
  - ProcessDocument class methods
  - PDF loading and processing
  - Text splitting (recursive, semantic)
  - VectorDB operations
  - RAG QA chain
  - Reranking

- **API Endpoints** (`test_api_endpoints.py`)
  - POST /api/v1/documento
  - POST /api/v1/busqueda_bdv
  - POST /api/v1/cadena_qa
  - POST /api/v1/cadena_rankeada

- **PDF Processing** (`test_pdf_processing.py`)
  - PyMuPDF text extraction
  - Document metadata handling

## 🔗 References

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-mock Documentation](https://pytest-mock.readthedocs.io/)
- [Pydantic Testing Guide](https://docs.pydantic.dev/latest/concepts/validation/)

## 📞 Need Help?

- Check existing test files for examples
- Review `conftest.py` for available fixtures
- See pytest output for detailed error messages

---

**Next Steps**: Continue implementing handler, service, and API endpoint tests following the same pattern!
