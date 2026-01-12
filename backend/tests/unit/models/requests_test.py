"""Unit tests for request models."""

import base64
import unittest

from pydantic import ValidationError

from app.models.requests.document_request import DocumentIngestRequest
from app.models.requests.search_request import DocumentSearchRequest, QuestionRequest


class TestDocumentIngestRequest(unittest.TestCase):
    """Test cases for DocumentIngestRequest model."""

    def test_valid_document_ingest_request(self):
        """Test creating a valid DocumentIngestRequest."""
        # Arrange
        valid_base64 = base64.b64encode(b"test content").decode("utf-8")

        # Act
        request = DocumentIngestRequest(
            title="test-document",
            document_type="pdf",
            document_content=valid_base64,
        )

        # Assert
        self.assertEqual(request.title, "test-document")
        self.assertEqual(request.document_type, "pdf")
        self.assertEqual(request.document_content, valid_base64)

    def test_document_ingest_request_with_default_type(self):
        """Test DocumentIngestRequest uses default document_type."""
        # Arrange
        valid_base64 = base64.b64encode(b"test content").decode("utf-8")

        # Act
        request = DocumentIngestRequest(
            title="test-document",
            document_content=valid_base64,
        )

        # Assert
        self.assertEqual(request.document_type, "documento-pdf")

    def test_document_ingest_request_missing_title_raises_validation_error(self):
        """Test DocumentIngestRequest raises ValidationError when title is missing."""
        # Arrange
        valid_base64 = base64.b64encode(b"test content").decode("utf-8")

        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            DocumentIngestRequest(document_content=valid_base64)

        self.assertIn("title", str(context.exception))

    def test_document_ingest_request_missing_content_raises_validation_error(self):
        """Test DocumentIngestRequest raises ValidationError when document_content is missing."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            DocumentIngestRequest(title="test-document")

        self.assertIn("document_content", str(context.exception))

    def test_document_ingest_request_invalid_base64_raises_validation_error(self):
        """Test DocumentIngestRequest raises ValidationError for invalid base64."""
        # Arrange
        invalid_base64 = "not-valid-base64!!!"

        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            DocumentIngestRequest(
                title="test-document",
                document_content=invalid_base64,
            )

        error_dict = context.exception.errors()[0]
        self.assertEqual(error_dict["type"], "value_error")
        self.assertIn("Invalid base64 encoding", str(error_dict["ctx"]["error"]))

    def test_document_ingest_request_serialization(self):
        """Test DocumentIngestRequest can be serialized to dict."""
        # Arrange
        valid_base64 = base64.b64encode(b"test content").decode("utf-8")
        request = DocumentIngestRequest(
            title="test-document",
            document_type="pdf",
            document_content=valid_base64,
        )

        # Act
        request_dict = request.model_dump()

        # Assert
        self.assertEqual(request_dict["title"], "test-document")
        self.assertEqual(request_dict["document_type"], "pdf")
        self.assertEqual(request_dict["document_content"], valid_base64)


class TestDocumentSearchRequest(unittest.TestCase):
    """Test cases for DocumentSearchRequest model."""

    def test_valid_document_search_request(self):
        """Test creating a valid DocumentSearchRequest."""
        # Act
        request = DocumentSearchRequest(
            query="What is ROS?",
            k_results=5,
            metadata_filter={"source": "manual"},
        )

        # Assert
        self.assertEqual(request.query, "What is ROS?")
        self.assertEqual(request.k_results, 5)
        self.assertEqual(request.metadata_filter, {"source": "manual"})

    def test_document_search_request_with_defaults(self):
        """Test DocumentSearchRequest uses default values."""
        # Act
        request = DocumentSearchRequest(query="test query")

        # Assert
        self.assertEqual(request.query, "test query")
        self.assertEqual(request.k_results, 4)
        self.assertEqual(request.metadata_filter, {})

    def test_document_search_request_missing_query_raises_validation_error(self):
        """Test DocumentSearchRequest raises ValidationError when query is missing."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            DocumentSearchRequest(k_results=5)

        self.assertIn("query", str(context.exception))

    def test_document_search_request_k_results_below_minimum_raises_validation_error(self):
        """Test DocumentSearchRequest raises ValidationError when k_results < 1."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            DocumentSearchRequest(query="test", k_results=0)

        error = context.exception.errors()[0]
        self.assertEqual(error["type"], "greater_than_equal")

    def test_document_search_request_k_results_above_maximum_raises_validation_error(self):
        """Test DocumentSearchRequest raises ValidationError when k_results > 10."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            DocumentSearchRequest(query="test", k_results=11)

        error = context.exception.errors()[0]
        self.assertEqual(error["type"], "less_than_equal")


class TestQuestionRequest(unittest.TestCase):
    """Test cases for QuestionRequest model."""

    def test_valid_question_request_standard_strategy(self):
        """Test creating a valid QuestionRequest with standard strategy."""
        # Act
        request = QuestionRequest(
            question="What is ROS?",
            strategy="standard",
            k_results=5,
        )

        # Assert
        self.assertEqual(request.question, "What is ROS?")
        self.assertEqual(request.strategy, "standard")
        self.assertEqual(request.k_results, 5)

    def test_valid_question_request_rerank_strategy(self):
        """Test creating a valid QuestionRequest with rerank strategy."""
        # Act
        request = QuestionRequest(
            question="What is ROS?",
            strategy="rerank",
            k_results=3,
        )

        # Assert
        self.assertEqual(request.question, "What is ROS?")
        self.assertEqual(request.strategy, "rerank")
        self.assertEqual(request.k_results, 3)

    def test_question_request_with_defaults(self):
        """Test QuestionRequest uses default values."""
        # Act
        request = QuestionRequest(question="test question")

        # Assert
        self.assertEqual(request.question, "test question")
        self.assertEqual(request.strategy, "standard")
        self.assertEqual(request.k_results, 4)
        self.assertEqual(request.metadata_filter, {})

    def test_question_request_missing_question_raises_validation_error(self):
        """Test QuestionRequest raises ValidationError when question is missing."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            QuestionRequest(strategy="standard")

        self.assertIn("question", str(context.exception))

    def test_question_request_empty_question_raises_validation_error(self):
        """Test QuestionRequest raises ValidationError when question is empty."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            QuestionRequest(question="")

        error = context.exception.errors()[0]
        self.assertIn("at least 1 character", str(error))

    def test_question_request_invalid_strategy_raises_validation_error(self):
        """Test QuestionRequest raises ValidationError for invalid strategy."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            QuestionRequest(question="test", strategy="invalid-strategy")

        error = context.exception.errors()[0]
        self.assertEqual(error["type"], "literal_error")

    def test_question_request_k_results_below_minimum_raises_validation_error(self):
        """Test QuestionRequest raises ValidationError when k_results < 1."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            QuestionRequest(question="test", k_results=0)

        error = context.exception.errors()[0]
        self.assertEqual(error["type"], "greater_than_equal")

    def test_question_request_k_results_above_maximum_raises_validation_error(self):
        """Test QuestionRequest raises ValidationError when k_results > 10."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            QuestionRequest(question="test", k_results=11)

        error = context.exception.errors()[0]
        self.assertEqual(error["type"], "less_than_equal")


if __name__ == "__main__":
    unittest.main()
