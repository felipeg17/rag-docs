"""
Unit tests for Pydantic request models.

Tests validation logic for:
- ProcessDocumentRequest
- SearchVectorDataBaseRequest
"""

import pytest
from pydantic import ValidationError

from app.procesar_documento.models.process_document_request import (
    ProcessDocumentRequest,
    SearchVectorDataBaseRequest,
)


# ============================================================================
# ProcessDocumentRequest Tests
# ============================================================================

class TestProcessDocumentRequest:
    """Test ProcessDocumentRequest model validation."""

    def test_valid_request_with_all_fields(self):
        """Test valid request with all fields provided."""
        request = ProcessDocumentRequest(
            title="Test Document",
            document_type="documento-pdf",
            document_chain="YmFzZTY0X2VuY29kZWRfcGRm",  # base64 encoded
        )

        assert request.title == "Test Document"
        assert request.document_type == "documento-pdf"
        assert request.document_chain == "YmFzZTY0X2VuY29kZWRfcGRm"

    def test_valid_request_with_default_document_type(self):
        """Test that document_type defaults to 'documento-pdf'."""
        request = ProcessDocumentRequest(
            title="Test Document",
            document_chain="YmFzZTY0X2VuY29kZWRfcGRm",
        )

        assert request.document_type == "documento-pdf"

    def test_missing_title_raises_validation_error(self):
        """Test that missing title raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessDocumentRequest(
                document_chain="YmFzZTY0X2VuY29kZWRfcGRm",
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("title",)
        assert errors[0]["type"] == "missing"

    def test_missing_document_chain_raises_validation_error(self):
        """Test that missing document_chain raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessDocumentRequest(
                title="Test Document",
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("document_chain",)
        assert errors[0]["type"] == "missing"

    def test_empty_title_is_valid(self):
        """Test that empty string title is technically valid (business logic may reject)."""
        request = ProcessDocumentRequest(
            title="",
            document_chain="YmFzZTY0X2VuY29kZWRfcGRm",
        )

        assert request.title == ""

    def test_none_document_type_uses_default(self):
        """Test that None document_type uses default value."""
        request = ProcessDocumentRequest(
            title="Test",
            document_type=None,
            document_chain="YmFzZTY0X2VuY29kZWRfcGRm",
        )

        assert request.document_type == "documento-pdf"

    def test_custom_document_type(self):
        """Test that custom document types are accepted."""
        request = ProcessDocumentRequest(
            title="Test",
            document_type="custom-doc-type",
            document_chain="YmFzZTY0X2VuY29kZWRfcGRm",
        )

        assert request.document_type == "custom-doc-type"


# ============================================================================
# SearchVectorDataBaseRequest Tests
# ============================================================================

class TestSearchVectorDataBaseRequest:
    """Test SearchVectorDataBaseRequest model validation."""

    def test_valid_request_with_all_fields(self):
        """Test valid request with all fields provided."""
        request = SearchVectorDataBaseRequest(
            title="Test Document",
            document_type="documento-pdf",
            query="What is this document about?",
            k_results=10,
            metadata_filter={"author": "John Doe"},
        )

        assert request.title == "Test Document"
        assert request.document_type == "documento-pdf"
        assert request.query == "What is this document about?"
        assert request.k_results == 10
        assert request.metadata_filter == {"author": "John Doe"}

    def test_all_fields_optional(self):
        """Test that all fields are optional and use defaults."""
        request = SearchVectorDataBaseRequest()

        assert request.title is None
        assert request.document_type == "documento-pdf"
        assert request.query is None
        assert request.k_results == 4
        assert request.metadata_filter == {}

    def test_partial_fields(self):
        """Test request with some fields provided."""
        request = SearchVectorDataBaseRequest(
            title="Test",
            query="test query",
        )

        assert request.title == "Test"
        assert request.query == "test query"
        assert request.document_type == "documento-pdf"  # default
        assert request.k_results == 4  # default
        assert request.metadata_filter == {}  # default

    def test_k_results_accepts_positive_integers(self):
        """Test that k_results accepts positive integers."""
        request = SearchVectorDataBaseRequest(k_results=100)
        assert request.k_results == 100

    def test_k_results_zero_is_valid(self):
        """Test that k_results=0 is technically valid (business logic may reject)."""
        request = SearchVectorDataBaseRequest(k_results=0)
        assert request.k_results == 0

    def test_empty_metadata_filter(self):
        """Test that empty dict is valid for metadata_filter."""
        request = SearchVectorDataBaseRequest(metadata_filter={})
        assert request.metadata_filter == {}

    def test_complex_metadata_filter(self):
        """Test that complex metadata filters are accepted."""
        complex_filter = {
            "tipo-documento": {"$eq": "documento-pdf"},
            "pagina": {"$gte": 5, "$lte": 10},
        }
        request = SearchVectorDataBaseRequest(metadata_filter=complex_filter)

        assert request.metadata_filter == complex_filter

    def test_none_values_use_defaults(self):
        """Test that None values use field defaults."""
        request = SearchVectorDataBaseRequest(
            title=None,
            document_type=None,
            query=None,
            k_results=None,
            metadata_filter=None,
        )

        assert request.title is None
        assert request.document_type == "documento-pdf"
        assert request.query is None
        assert request.k_results == 4
        assert request.metadata_filter == {}

    def test_empty_string_query(self):
        """Test that empty string query is valid."""
        request = SearchVectorDataBaseRequest(query="")
        assert request.query == ""

    def test_model_serialization(self):
        """Test that model can be serialized to dict."""
        request = SearchVectorDataBaseRequest(
            title="Test",
            query="test query",
            k_results=5,
        )

        data = request.model_dump()

        assert isinstance(data, dict)
        assert data["title"] == "Test"
        assert data["query"] == "test query"
        assert data["k_results"] == 5
        assert data["document_type"] == "documento-pdf"
        assert data["metadata_filter"] == {}

    def test_model_json_serialization(self):
        """Test that model can be serialized to JSON."""
        request = SearchVectorDataBaseRequest(
            title="Test",
            query="test query",
        )

        json_str = request.model_dump_json()

        assert isinstance(json_str, str)
        assert "Test" in json_str
        assert "test query" in json_str
