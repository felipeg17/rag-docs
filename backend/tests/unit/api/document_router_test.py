import json
import unittest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from langchain.schema import Document

from app.core.dependencies import (
    get_ingestion_service,
    get_qa_service,
    get_rerank_service,
    get_vector_db_repository,
)
from main import app

from ..services.document.pdf_loader_test import FIXTURES_PATH


class TestProcessDocumentController(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        golden_responses_path = FIXTURES_PATH / "golden_responses"

        # Load sample PDF base64
        with open(golden_responses_path / "sample_pdf_base64.json", "r") as f:
            cls.sample_pdf_data = json.load(f)

        # Load vector DB search response
        with open(golden_responses_path / "chromadb_search_response.json", "r") as f:
            cls.vdb_search_response = json.load(f)

        # Load QA response
        with open(golden_responses_path / "llm_qa_response.json", "r") as f:
            cls.qa_response = json.load(f)

        # Load rerank QA response
        with open(golden_responses_path / "rerank_qa_complete_response.json", "r") as f:
            cls.rerank_qa_response = json.load(f)

    def setUp(self):
        """Set up mocks for each test."""
        # Create mock services
        self.mock_ingestion_service = MagicMock()
        self.mock_vdb_repository = MagicMock()
        self.mock_qa_service = MagicMock()
        self.mock_rerank_service = MagicMock()

        # Override dependencies with lambdas (FastAPI requires callables)
        app.dependency_overrides[get_ingestion_service] = lambda: self.mock_ingestion_service
        app.dependency_overrides[get_vector_db_repository] = lambda: self.mock_vdb_repository
        app.dependency_overrides[get_qa_service] = lambda: self.mock_qa_service
        app.dependency_overrides[get_rerank_service] = lambda: self.mock_rerank_service

        # Create test client
        self.client = TestClient(app)

    def tearDown(self):
        """Clear dependency overrides after each test."""
        app.dependency_overrides.clear()

    def test_document_ingestion_new_document(self):
        # Arrange
        # Document doesn't exist, so it will be created
        self.mock_vdb_repository.check_document_exists.return_value = False
        self.mock_ingestion_service.ingest_document.return_value = True

        payload = {
            "title": "test-document",
            "document_type": "documento-pdf",
            "document_content": self.sample_pdf_data["base64_content"][:100],
        }

        # Act
        response = self.client.post("/api/v1/documents", json=payload)

        # Assert
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        self.assertIn("document_id", response_data)
        self.assertIn("title", response_data)
        self.assertEqual(response_data["status"], "created")
        self.assertEqual(response_data["title"], "test-document")
        self.mock_ingestion_service.ingest_document.assert_called_once()
        self.mock_vdb_repository.check_document_exists.assert_called_once()

    def test_document_ingestion_existing_document(self):
        # Arrange
        # Document already exists, so it will return 200 and "updated" status
        self.mock_vdb_repository.check_document_exists.return_value = True

        payload = {
            "title": "existing-document",
            "document_type": "documento-pdf",
            "document_content": self.sample_pdf_data["base64_content"][:100],
        }

        # Act
        response = self.client.post("/api/v1/documents", json=payload)

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("document_id", response_data)
        self.assertEqual(response_data["status"], "updated")
        self.assertEqual(response_data["title"], "existing-document")
        # Should NOT call ingestion service for existing documents
        self.mock_ingestion_service.ingest_document.assert_not_called()
        self.mock_vdb_repository.check_document_exists.assert_called_once()

    def test_document_ingestion_missing_parameters(self):
        # Arrange
        payload = {
            "document_type": "pdf",
            "document_content": "base64content",
            # Missing required "title" field
        }

        # Act
        response = self.client.post("/api/v1/documents", json=payload)

        # Assert
        self.assertEqual(response.status_code, 422)

    def test_document_ingestion_service_error(self):
        """Test document ingestion endpoint handles service errors."""
        # Arrange
        self.mock_vdb_repository.check_document_exists.return_value = False
        self.mock_ingestion_service.ingest_document.side_effect = Exception("Service error")

        # Use valid base64 content (this is "test content" encoded)
        payload = {
            "title": "test-document",
            "document_type": "documento-pdf",
            "document_content": "dGVzdCBjb250ZW50",
        }

        # Act
        response = self.client.post("/api/v1/documents", json=payload)

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIn("detail", response.json())

    def test_vdb_search_returns_results(self):
        # Arrange - Convert golden response to Document objects with scores
        search_results = []
        for result_data in self.vdb_search_response["results"]:
            doc = Document(
                page_content=result_data["page_content"],
                metadata=result_data["metadata"],
            )
            search_results.append((doc, result_data["score"]))

        self.mock_vdb_repository.similarity_search_with_score.return_value = search_results
        self.mock_vdb_repository.check_document_exists.return_value = True

        document_id = "test-document"
        payload = {
            "query": "What is ROS and what is it used for?",
            "k_results": 4,
            "metadata_filter": {},
        }

        # Act
        response = self.client.post(f"/api/v1/documents/{document_id}/search", json=payload)

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("results", response_data)
        self.assertIn("query", response_data)
        self.assertIn("total_results", response_data)
        self.assertEqual(response_data["query"], "What is ROS and what is it used for?")
        self.assertEqual(response_data["total_results"], 4)
        self.assertEqual(len(response_data["results"]), 4)

        # Verify first result structure - should be SearchResultItem
        first_result = response_data["results"][0]
        self.assertIsInstance(first_result, dict)
        self.assertIn("content", first_result)
        self.assertIn("score", first_result)
        self.assertIn("metadata", first_result)
        self.assertIsInstance(first_result["score"], float)

    def test_qa_endpoint_success(self):
        # Arrange - Use golden QA response
        source_docs = []
        for doc_data in self.qa_response["source_documents"]:
            doc = Document(
                page_content=doc_data["page_content"],
                metadata=doc_data["metadata"],
            )
            source_docs.append(doc)

        qa_result = {
            "result": self.qa_response["response"]["content"],
            "source_documents": source_docs,
        }
        self.mock_qa_service.answer_question.return_value = qa_result
        self.mock_vdb_repository.check_document_exists.return_value = True

        document_id = "test-document"
        payload = {
            "question": "What is ROS and what is it used for?",
            "strategy": "standard",
            "k_results": 4,
            "metadata_filter": {},
        }

        # Act
        response = self.client.post(f"/api/v1/documents/{document_id}/ask", json=payload)

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        # Verify response structure
        self.assertIn("question", response_data)
        self.assertIn("answer", response_data)
        self.assertIn("source_documents", response_data)
        self.assertIn("document_id", response_data)
        self.assertIn("strategy", response_data)

        # Verify content
        self.assertEqual(response_data["question"], "What is ROS and what is it used for?")
        self.assertEqual(response_data["document_id"], document_id)
        self.assertEqual(response_data["strategy"], "standard")
        self.assertIsInstance(response_data["answer"], str)
        self.assertGreater(len(response_data["answer"]), 0)
        self.assertIsInstance(response_data["source_documents"], list)
        self.assertEqual(len(response_data["source_documents"]), 4)

    def test_qa_endpoint_service_error_returns_500(self):
        # Arrange
        self.mock_vdb_repository.check_document_exists.return_value = True
        self.mock_qa_service.answer_question.side_effect = Exception("LLM service error")

        document_id = "test-document"
        payload = {
            "question": "test query",
            "strategy": "standard",
            "k_results": 4,
            "metadata_filter": {},
        }

        # Act
        response = self.client.post(f"/api/v1/documents/{document_id}/ask", json=payload)

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIn("detail", response.json())

    def test_rerank_qa_endpoint_success(self):
        # Arrange - Use golden rerank QA response
        # answer_question returns the answer string directly
        answer_text = self.rerank_qa_response["response"]["content"]
        self.mock_rerank_service.answer_question.return_value = answer_text
        self.mock_vdb_repository.check_document_exists.return_value = True

        document_id = "test-document"
        payload = {
            "question": "What is ROS and what is it used for?",
            "strategy": "rerank",
            "k_results": 4,
            "metadata_filter": {},
        }

        # Act
        response = self.client.post(f"/api/v1/documents/{document_id}/ask", json=payload)

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        # Verify response structure
        self.assertIn("question", response_data)
        self.assertIn("answer", response_data)
        self.assertIn("document_id", response_data)
        self.assertIn("strategy", response_data)
        self.assertIn("source_documents", response_data)

        # Verify content
        self.assertEqual(response_data["question"], "What is ROS and what is it used for?")
        self.assertEqual(response_data["document_id"], document_id)
        self.assertEqual(response_data["strategy"], "rerank")
        self.assertIsInstance(response_data["answer"], str)
        self.assertGreater(len(response_data["answer"]), 0)
        # Rerank doesn't return source documents
        self.assertEqual(len(response_data["source_documents"]), 0)

    def test_rerank_qa_endpoint_service_error(self):
        # Arrange
        self.mock_vdb_repository.check_document_exists.return_value = True
        self.mock_rerank_service.answer_question.side_effect = Exception("Rerank service error")

        document_id = "test-document"
        payload = {
            "question": "test query",
            "strategy": "rerank",
            "k_results": 4,
            "metadata_filter": {},
        }

        # Act
        response = self.client.post(f"/api/v1/documents/{document_id}/ask", json=payload)

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIn("detail", response.json())

    def test_qa_endpoint_document_not_found_returns_404(self):
        # Arrange
        self.mock_vdb_repository.check_document_exists.return_value = False

        document_id = "non-existent-document"
        payload = {"question": "test query", "strategy": "standard", "k_results": 4}

        # Act
        response = self.client.post(f"/api/v1/documents/{document_id}/ask", json=payload)

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertIn("detail", response.json())
        self.assertIn("not found", response.json()["detail"].lower())

    def test_search_endpoint_document_not_found_returns_empty_results(self):
        # Arrange
        self.mock_vdb_repository.check_document_exists.return_value = False

        document_id = "non-existent-document"
        payload = {
            "query": "test query",
            "k_results": 4,
            "metadata_filter": {},
        }

        # Act
        response = self.client.post(f"/api/v1/documents/{document_id}/search", json=payload)

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertIn("detail", response.json())
        self.assertIn("not found", response.json()["detail"].lower())


if __name__ == "__main__":
    unittest.main()
