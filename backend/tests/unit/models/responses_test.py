"""Unit tests for response models."""

import unittest

from pydantic import ValidationError

from app.models.responses.document_response import DocumentIngestResponse
from app.models.responses.qa_response import QuestionAnswerResponse, SourceDocument
from app.models.responses.search_response import DocumentSearchResponse, SearchResultItem


class TestDocumentIngestResponse(unittest.TestCase):
    """Test cases for DocumentIngestResponse model."""

    def test_valid_document_ingest_response_created(self):
        """Test creating a valid DocumentIngestResponse with 'created' status."""
        # Act
        response = DocumentIngestResponse(
            document_id="123e4567-e89b-12d3-a456-426614174000",
            title="test-document",
            status="created",
            message="Document created successfully",
        )

        # Assert
        self.assertEqual(response.document_id, "123e4567-e89b-12d3-a456-426614174000")
        self.assertEqual(response.title, "test-document")
        self.assertEqual(response.status, "created")
        self.assertEqual(response.message, "Document created successfully")

    def test_valid_document_ingest_response_updated(self):
        """Test creating a valid DocumentIngestResponse with 'updated' status."""
        # Act
        response = DocumentIngestResponse(
            document_id="123e4567-e89b-12d3-a456-426614174000",
            title="existing-document",
            status="updated",
            message="Document updated successfully",
        )

        # Assert
        self.assertEqual(response.status, "updated")
        self.assertEqual(response.message, "Document updated successfully")

    def test_document_ingest_response_missing_document_id_raises_validation_error(self):
        """Test DocumentIngestResponse raises ValidationError when document_id is missing."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            DocumentIngestResponse(
                title="test-document",
                status="created",
                message="test message",
            )

        self.assertIn("document_id", str(context.exception))

    def test_document_ingest_response_missing_title_raises_validation_error(self):
        """Test DocumentIngestResponse raises ValidationError when title is missing."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            DocumentIngestResponse(
                document_id="123e4567-e89b-12d3-a456-426614174000",
                status="created",
                message="test message",
            )

        self.assertIn("title", str(context.exception))

    def test_document_ingest_response_invalid_status_raises_validation_error(self):
        """Test DocumentIngestResponse raises ValidationError for invalid status."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            DocumentIngestResponse(
                document_id="123e4567-e89b-12d3-a456-426614174000",
                title="test-document",
                status="invalid-status",
                message="test message",
            )

        error = context.exception.errors()[0]
        self.assertEqual(error["type"], "literal_error")

    def test_document_ingest_response_serialization(self):
        """Test DocumentIngestResponse can be serialized to dict."""
        # Arrange
        response = DocumentIngestResponse(
            document_id="123e4567-e89b-12d3-a456-426614174000",
            title="test-document",
            status="created",
            message="Document created successfully",
        )

        # Act
        response_dict = response.model_dump()

        # Assert
        self.assertEqual(response_dict["document_id"], "123e4567-e89b-12d3-a456-426614174000")
        self.assertEqual(response_dict["title"], "test-document")
        self.assertEqual(response_dict["status"], "created")
        self.assertEqual(response_dict["message"], "Document created successfully")


class TestSearchResultItem(unittest.TestCase):
    """Test cases for SearchResultItem model."""

    def test_valid_search_result_item(self):
        """Test creating a valid SearchResultItem."""
        # Act
        item = SearchResultItem(
            content="This is a test document chunk",
            score=0.95,
            metadata={"page": 1, "source": "test.pdf"},
        )

        # Assert
        self.assertEqual(item.content, "This is a test document chunk")
        self.assertEqual(item.score, 0.95)
        self.assertEqual(item.metadata, {"page": 1, "source": "test.pdf"})

    def test_search_result_item_missing_content_raises_validation_error(self):
        """Test SearchResultItem raises ValidationError when content is missing."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            SearchResultItem(score=0.95, metadata={"page": 1})

        self.assertIn("content", str(context.exception))

    def test_search_result_item_missing_score_raises_validation_error(self):
        """Test SearchResultItem raises ValidationError when score is missing."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            SearchResultItem(content="test content", metadata={"page": 1})

        self.assertIn("score", str(context.exception))

    def test_search_result_item_score_below_minimum_raises_validation_error(self):
        """Test SearchResultItem raises ValidationError when score < 0.0."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            SearchResultItem(content="test content", score=-0.1, metadata={})

        error = context.exception.errors()[0]
        self.assertEqual(error["type"], "greater_than_equal")

    def test_search_result_item_score_above_maximum_raises_validation_error(self):
        """Test SearchResultItem raises ValidationError when score > 1.0."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            SearchResultItem(content="test content", score=1.1, metadata={})

        error = context.exception.errors()[0]
        self.assertEqual(error["type"], "less_than_equal")

    def test_search_result_item_serialization(self):
        """Test SearchResultItem can be serialized to dict."""
        # Arrange
        item = SearchResultItem(
            content="test content",
            score=0.85,
            metadata={"page": 2},
        )

        # Act
        item_dict = item.model_dump()

        # Assert
        self.assertEqual(item_dict["content"], "test content")
        self.assertEqual(item_dict["score"], 0.85)
        self.assertEqual(item_dict["metadata"], {"page": 2})


class TestDocumentSearchResponse(unittest.TestCase):
    """Test cases for DocumentSearchResponse model."""

    def test_valid_document_search_response(self):
        """Test creating a valid DocumentSearchResponse."""
        # Arrange
        results = [
            SearchResultItem(content="chunk 1", score=0.95, metadata={"page": 1}),
            SearchResultItem(content="chunk 2", score=0.85, metadata={"page": 2}),
        ]

        # Act
        response = DocumentSearchResponse(
            query="What is ROS?",
            results=results,
            total_results=2,
        )

        # Assert
        self.assertEqual(response.query, "What is ROS?")
        self.assertEqual(len(response.results), 2)
        self.assertEqual(response.total_results, 2)
        self.assertEqual(response.results[0].content, "chunk 1")
        self.assertEqual(response.results[1].score, 0.85)

    def test_document_search_response_with_empty_results(self):
        """Test DocumentSearchResponse with empty results list."""
        # Act
        response = DocumentSearchResponse(
            query="test query",
            results=[],
            total_results=0,
        )

        # Assert
        self.assertEqual(response.query, "test query")
        self.assertEqual(len(response.results), 0)
        self.assertEqual(response.total_results, 0)

    def test_document_search_response_missing_query_raises_validation_error(self):
        """Test DocumentSearchResponse raises ValidationError when query is missing."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            DocumentSearchResponse(results=[], total_results=0)

        self.assertIn("query", str(context.exception))

    def test_document_search_response_missing_results_raises_validation_error(self):
        """Test DocumentSearchResponse raises ValidationError when results is missing."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            DocumentSearchResponse(query="test", total_results=0)

        self.assertIn("results", str(context.exception))

    def test_document_search_response_serialization(self):
        """Test DocumentSearchResponse can be serialized to dict."""
        # Arrange
        results = [
            SearchResultItem(content="chunk 1", score=0.95, metadata={"page": 1}),
        ]
        response = DocumentSearchResponse(
            query="test query",
            results=results,
            total_results=1,
        )

        # Act
        response_dict = response.model_dump()

        # Assert
        self.assertEqual(response_dict["query"], "test query")
        self.assertEqual(len(response_dict["results"]), 1)
        self.assertEqual(response_dict["results"][0]["content"], "chunk 1")
        self.assertEqual(response_dict["total_results"], 1)


class TestSourceDocument(unittest.TestCase):
    """Test cases for SourceDocument model."""

    def test_valid_source_document_without_score(self):
        """Test creating a valid SourceDocument without score."""
        # Act
        doc = SourceDocument(
            page_content="Document content",
            metadata={"page": 1, "source": "test.pdf"},
        )

        # Assert
        self.assertEqual(doc.page_content, "Document content")
        self.assertEqual(doc.metadata, {"page": 1, "source": "test.pdf"})
        self.assertIsNone(doc.score)

    def test_valid_source_document_with_score(self):
        """Test creating a valid SourceDocument with score."""
        # Act
        doc = SourceDocument(
            page_content="Document content",
            metadata={"page": 1},
            score=0.92,
        )

        # Assert
        self.assertEqual(doc.page_content, "Document content")
        self.assertEqual(doc.score, 0.92)

    def test_source_document_missing_page_content_raises_validation_error(self):
        """Test SourceDocument raises ValidationError when page_content is missing."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            SourceDocument(metadata={"page": 1})

        self.assertIn("page_content", str(context.exception))

    def test_source_document_missing_metadata_raises_validation_error(self):
        """Test SourceDocument raises ValidationError when metadata is missing."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            SourceDocument(page_content="test content")

        self.assertIn("metadata", str(context.exception))

    def test_source_document_serialization(self):
        """Test SourceDocument can be serialized to dict."""
        # Arrange
        doc = SourceDocument(
            page_content="test content",
            metadata={"page": 1},
            score=0.88,
        )

        # Act
        doc_dict = doc.model_dump()

        # Assert
        self.assertEqual(doc_dict["page_content"], "test content")
        self.assertEqual(doc_dict["metadata"], {"page": 1})
        self.assertEqual(doc_dict["score"], 0.88)


class TestQuestionAnswerResponse(unittest.TestCase):
    """Test cases for QuestionAnswerResponse model."""

    def test_valid_question_answer_response_standard_strategy(self):
        """Test creating a valid QuestionAnswerResponse with standard strategy."""
        # Arrange
        source_docs = [
            SourceDocument(page_content="Content 1", metadata={"page": 1}, score=0.95),
            SourceDocument(page_content="Content 2", metadata={"page": 2}, score=0.85),
        ]

        # Act
        response = QuestionAnswerResponse(
            question="What is ROS?",
            answer="ROS is a robotics framework",
            document_id="test-doc",
            strategy="standard",
            source_documents=source_docs,
        )

        # Assert
        self.assertEqual(response.question, "What is ROS?")
        self.assertEqual(response.answer, "ROS is a robotics framework")
        self.assertEqual(response.document_id, "test-doc")
        self.assertEqual(response.strategy, "standard")
        self.assertEqual(len(response.source_documents), 2)

    def test_valid_question_answer_response_rerank_strategy(self):
        """Test creating a valid QuestionAnswerResponse with rerank strategy."""
        # Act
        response = QuestionAnswerResponse(
            question="What is ROS?",
            answer="ROS is a robotics framework",
            document_id="test-doc",
            strategy="rerank",
            source_documents=[],
        )

        # Assert
        self.assertEqual(response.strategy, "rerank")
        self.assertEqual(len(response.source_documents), 0)

    def test_question_answer_response_with_default_source_documents(self):
        """Test QuestionAnswerResponse uses default empty list for source_documents."""
        # Act
        response = QuestionAnswerResponse(
            question="test question",
            answer="test answer",
            document_id="test-doc",
            strategy="standard",
        )

        # Assert
        self.assertEqual(response.source_documents, [])

    def test_question_answer_response_with_null_answer(self):
        """Test QuestionAnswerResponse allows null answer."""
        # Act
        response = QuestionAnswerResponse(
            question="test question",
            answer=None,
            document_id="test-doc",
            strategy="standard",
        )

        # Assert
        self.assertIsNone(response.answer)

    def test_question_answer_response_missing_question_raises_validation_error(self):
        """Test QuestionAnswerResponse raises ValidationError when question is missing."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            QuestionAnswerResponse(
                answer="test answer",
                document_id="test-doc",
                strategy="standard",
            )

        self.assertIn("question", str(context.exception))

    def test_question_answer_response_missing_document_id_raises_validation_error(self):
        """Test QuestionAnswerResponse raises ValidationError when document_id is missing."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            QuestionAnswerResponse(
                question="test question",
                answer="test answer",
                strategy="standard",
            )

        self.assertIn("document_id", str(context.exception))

    def test_question_answer_response_invalid_strategy_raises_validation_error(self):
        """Test QuestionAnswerResponse raises ValidationError for invalid strategy."""
        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            QuestionAnswerResponse(
                question="test",
                answer="answer",
                document_id="doc",
                strategy="invalid-strategy",
            )

        error = context.exception.errors()[0]
        self.assertEqual(error["type"], "literal_error")

    def test_question_answer_response_serialization(self):
        """Test QuestionAnswerResponse can be serialized to dict."""
        # Arrange
        source_docs = [
            SourceDocument(page_content="Content", metadata={"page": 1}),
        ]
        response = QuestionAnswerResponse(
            question="What is ROS?",
            answer="ROS is a robotics framework",
            document_id="test-doc",
            strategy="standard",
            source_documents=source_docs,
        )

        # Act
        response_dict = response.model_dump()

        # Assert
        self.assertEqual(response_dict["question"], "What is ROS?")
        self.assertEqual(response_dict["answer"], "ROS is a robotics framework")
        self.assertEqual(response_dict["document_id"], "test-doc")
        self.assertEqual(response_dict["strategy"], "standard")
        self.assertEqual(len(response_dict["source_documents"]), 1)


if __name__ == "__main__":
    unittest.main()
