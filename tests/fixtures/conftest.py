"""
Pytest fixtures for RAG-docs unit tests.

This module provides reusable fixtures for:
- Mock external services (OpenAI LLM, ChromaDB, Cohere)
- Golden response fixtures (embeddings, VectorDB results, reranking)
- Sample request objects
- Test documents
"""

import json
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock

import pytest


# ============================================================================
# Path Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def test_documents_dir(project_root: Path) -> Path:
    """Return the path to test documents directory."""
    return project_root / "documents"


@pytest.fixture(scope="session")
def golden_responses_dir() -> Path:
    """Return the path to golden responses directory."""
    return Path(__file__).parent / "golden_responses"


# ============================================================================
# Golden Response Loader
# ============================================================================

def load_golden_response(filename: str, golden_responses_dir: Path) -> Dict[str, Any]:
    """
    Load a golden response from JSON file.

    Args:
        filename: Name of the JSON file (e.g., "embedding_response.json")
        golden_responses_dir: Path to golden responses directory

    Returns:
        Dictionary containing the golden response
    """
    filepath = golden_responses_dir / filename
    if not filepath.exists():
        raise FileNotFoundError(
            f"Golden response file not found: {filepath}\n"
            f"Run the golden response generator script to create it."
        )

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def load_golden(golden_responses_dir: Path):
    """Fixture that returns a function to load golden responses."""
    def _load(filename: str) -> Dict[str, Any]:
        return load_golden_response(filename, golden_responses_dir)
    return _load


# ============================================================================
# Sample Test Documents
# ============================================================================

@pytest.fixture
def sample_pdf_bytes(test_documents_dir: Path) -> bytes:
    """
    Return bytes of a sample PDF for testing.
    Uses the smallest PDF from the documents directory.
    """
    # Use a small PDF for fast tests
    pdf_path = test_documents_dir / "Prueba_tecnica.pdf"

    # Fallback to any PDF if specific one doesn't exist
    if not pdf_path.exists():
        pdf_files = list(test_documents_dir.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF files found in documents directory")
        pdf_path = pdf_files[0]

    with open(pdf_path, "rb") as f:
        return f.read()


@pytest.fixture
def sample_pdf_base64(sample_pdf_bytes: bytes) -> str:
    """Return base64-encoded PDF string for testing."""
    import base64
    return base64.b64encode(sample_pdf_bytes).decode("utf-8")


# ============================================================================
# Sample Request Objects
# ============================================================================

@pytest.fixture
def sample_process_document_request() -> Dict[str, Any]:
    """Return a sample ProcessDocumentRequest as dict."""
    return {
        "title": "test_document",
        "document_type": "documento-pdf",
        "document_chain": "base64_encoded_pdf_here",  # Will be replaced in tests
    }


@pytest.fixture
def sample_search_request() -> Dict[str, Any]:
    """Return a sample SearchVectorDataBaseRequest as dict."""
    return {
        "title": "test_document",
        "document_type": "documento-pdf",
        "query": "What is the main topic of this document?",
        "k_results": 4,
        "metadata_filter": {},
    }


# ============================================================================
# Mock External Services - OpenAI LLM
# ============================================================================

@pytest.fixture
def mock_openai_llm():
    """
    Mock OpenAI ChatGPT LLM responses.

    Returns a mock that simulates LLM behavior for testing.
    """
    mock_llm = MagicMock()

    # Mock the invoke method to return a predictable response
    mock_llm.invoke.return_value = Mock(
        content="This is a test response from the LLM. The document discusses testing strategies."
    )

    # Mock the generate method if needed
    mock_llm.generate.return_value = Mock(
        generations=[[Mock(text="Test LLM response")]]
    )

    return mock_llm


# ============================================================================
# Mock External Services - OpenAI Embeddings (with Golden Responses)
# ============================================================================

@pytest.fixture
def mock_openai_embeddings(load_golden):
    """
    Mock OpenAI embeddings with golden response.

    Uses pre-recorded embeddings for deterministic testing.
    """
    mock_embeddings = MagicMock()

    # Load golden embedding response
    try:
        golden_data = load_golden("embedding_response.json")
        embedding_vector = golden_data.get("embedding", [0.1] * 100)
    except (FileNotFoundError, KeyError):
        # Fallback: Use a fake embedding vector
        embedding_vector = [0.1] * 100  # Simplified dimension for tests

    # Mock the embed_query method
    mock_embeddings.embed_query.return_value = embedding_vector

    # Mock the embed_documents method
    mock_embeddings.embed_documents.return_value = [embedding_vector]

    return mock_embeddings


# ============================================================================
# Mock External Services - ChromaDB (with Golden Responses)
# ============================================================================

@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB HTTP client."""
    mock_client = MagicMock()

    # Mock heartbeat
    mock_client.heartbeat.return_value = True

    # Mock collection operations
    mock_collection = MagicMock()
    mock_collection.name = "rag-docs"
    mock_client.get_collection.return_value = mock_collection
    mock_client.create_collection.return_value = mock_collection

    return mock_client


@pytest.fixture
def mock_chroma_vdb(load_golden):
    """
    Mock ChromaDB vector database with golden responses.

    Uses pre-recorded search results for deterministic testing.
    """
    from langchain.schema import Document

    mock_vdb = MagicMock()

    # Load golden VDB search response
    try:
        golden_data = load_golden("chromadb_search_response.json")
        raw_results = golden_data.get("results", [])

        # Convert golden response format to (Document, score) tuples
        search_results = [
            (
                Document(
                    page_content=result["page_content"],
                    metadata=result["metadata"]
                ),
                result["score"]
            )
            for result in raw_results
        ]
    except (FileNotFoundError, KeyError):
        # Fallback: Create a fake search result
        search_results = [
            (
                Document(
                    page_content="This is test content from page 1",
                    metadata={
                        "titulo": "test_document",
                        "tipo-documento": "documento-pdf",
                        "pagina": 0,
                    }
                ),
                0.85  # similarity score
            )
        ]

    # Mock similarity_search_with_score
    mock_vdb.similarity_search_with_score.return_value = search_results

    # Mock as_retriever
    mock_retriever = MagicMock()
    mock_retriever.get_relevant_documents.return_value = [doc for doc, score in search_results]
    mock_vdb.as_retriever.return_value = mock_retriever

    # Mock add_documents
    mock_vdb.add_documents.return_value = None

    # Mock get (for checking document existence)
    mock_vdb.get.return_value = {"ids": []}  # Empty by default

    return mock_vdb


# ============================================================================
# Mock External Services - Cohere Reranking (with Golden Responses)
# ============================================================================

@pytest.fixture
def mock_cohere_reranker(load_golden):
    """
    Mock Cohere reranker with golden response.

    Uses pre-recorded reranking results for deterministic testing.
    """
    from langchain.schema import Document

    mock_reranker = MagicMock()

    # Load golden reranking response
    try:
        golden_data = load_golden("cohere_rerank_response.json")
        raw_docs = golden_data.get("reranked_documents", [])

        # Convert golden response format to Document objects
        reranked_docs = [
            Document(
                page_content=doc["page_content"],
                metadata=doc["metadata"]
            )
            for doc in raw_docs
        ]
    except (FileNotFoundError, KeyError):
        # Fallback: Return documents in same order
        reranked_docs = [
            Document(
                page_content="Reranked content 1",
                metadata={"titulo": "test_document", "pagina": 0}
            )
        ]

    mock_reranker.compress_documents.return_value = reranked_docs

    return mock_reranker


# ============================================================================
# Mock External Services - PyMuPDF
# ============================================================================

@pytest.fixture
def mock_fitz_document():
    """
    Mock PyMuPDF (fitz) document for PDF processing tests.

    Simulates PDF text extraction without requiring real PDF parsing.
    """
    mock_doc = MagicMock()

    # Mock page_count
    mock_doc.page_count = 3

    # Mock load_page method
    def mock_load_page(page_num: int):
        mock_page = MagicMock()
        mock_page.get_text.return_value = f"This is the content of page {page_num + 1}."
        return mock_page

    mock_doc.load_page.side_effect = mock_load_page

    return mock_doc


# ============================================================================
# Composite Fixtures - Full ProcessDocument Mock Setup
# ============================================================================

@pytest.fixture
def mock_process_document_services(
    mock_openai_llm,
    mock_openai_embeddings,
    mock_chroma_client,
    mock_chroma_vdb,
):
    """
    Composite fixture that provides all mocked services for ProcessDocument.

    Use this when you need to test ProcessDocument with all dependencies mocked.
    """
    return {
        "llm": mock_openai_llm,
        "embeddings": mock_openai_embeddings,
        "chroma_client": mock_chroma_client,
        "chroma_vdb": mock_chroma_vdb,
    }
