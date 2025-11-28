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
        # ingest_document returns a truthy value for new documents
        self.mock_ingestion_service.ingest_document.return_value = True

        payload = {
            "title": "test-document",
            "document_type": "documento-pdf",
            "document_content": self.sample_pdf_data["base64_content"][:100],
        }

        # Act
        response = self.client.post("/rag-docs/api/v1/document", json=payload)

        # Assert
        self.assertEqual(response.status_code, 201)
        self.assertIn("query_id", response.json())
        self.mock_ingestion_service.ingest_document.assert_called_once()

    def test_document_ingestion_existing_document(self):
        # Arrange
        # ingest_document returns a falsy value for existing documents
        self.mock_ingestion_service.ingest_document.return_value = False

        payload = {
            "title": "existing-document",
            "document_type": "documento-pdf",
            "document_content": self.sample_pdf_data["base64_content"][:100],
        }

        # Act
        response = self.client.post("/rag-docs/api/v1/document", json=payload)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertIn("query_id", response.json())
        self.assertFalse(response.json()["status"])
        self.mock_ingestion_service.ingest_document.assert_called_once()

    def test_document_ingestion_missing_parameters(self):
        # Arrange
        payload = {
            "document_type": "documento-pdf",
            "document_content": "base64content",
        }

        # Act
        response = self.client.post("/rag-docs/api/v1/document", json=payload)

        # Assert
        self.assertEqual(response.status_code, 422)

    def test_document_ingestion_service_error(self):
        """Test document ingestion endpoint handles service errors."""
        # Arrange
        self.mock_ingestion_service.ingest_document.side_effect = Exception("Service error")

        payload = {
            "title": "test-document",
            "document_type": "documento-pdf",
            "document_content": "base64content",
        }

        # Act
        response = self.client.post("/rag-docs/api/v1/document", json=payload)

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

        payload = {
            "query": "What is ROS and what is it used for?",
            "document_type": "documento-pdf",
            "k_results": 4,
        }

        # Act
        response = self.client.post("/rag-docs/api/v1/vdb_result", json=payload)

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("results", response_data)
        self.assertEqual(len(response_data["results"]), 4)

        # Verify first result structure - it's a tuple [document_dict, score]
        first_result = response_data["results"][0]
        self.assertIsInstance(first_result, list)
        self.assertEqual(len(first_result), 2)

        # First element is document dict, second is score
        doc_dict = first_result[0]
        score = first_result[1]
        self.assertIn("page_content", doc_dict)
        self.assertIn("metadata", doc_dict)
        self.assertIsInstance(score, float)

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

        payload = {
            "query": "What is ROS and what is it used for?",
            "document_type": "documento-pdf",
            "k_results": 4,
        }

        # Act
        response = self.client.post("/rag-docs/api/v1/qa", json=payload)

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        # Verify response structure
        self.assertIn("query", response_data)
        self.assertIn("result", response_data)
        self.assertIn("source_documents", response_data)

        # Verify content
        self.assertEqual(response_data["query"], "What is ROS and what is it used for?")
        self.assertIsInstance(response_data["result"], str)
        self.assertGreater(len(response_data["result"]), 0)
        self.assertIsInstance(response_data["source_documents"], list)
        self.assertEqual(len(response_data["source_documents"]), 4)

    def test_qa_endpoint_service_error_returns_500(self):
        # Arrange
        self.mock_qa_service.answer_question.side_effect = Exception("LLM service error")

        payload = {"query": "test query", "k_results": 4}

        # Act
        response = self.client.post("/rag-docs/api/v1/qa", json=payload)

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIn("detail", response.json())

    def test_rerank_qa_endpoint_success(self):
        # Arrange - Use golden rerank QA response
        # answer_question returns the answer string directly
        answer_text = self.rerank_qa_response["response"]["content"]
        self.mock_rerank_service.answer_question.return_value = answer_text
        self.mock_vdb_repository.check_document_exists.return_value = True

        payload = {
            "query": "What is ROS and what is it used for?",
            "document_type": "documento-pdf",
            "k_results": 4,
        }

        # Act
        response = self.client.post("/rag-docs/api/v1/qa_ranked", json=payload)

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        # Verify response structure
        self.assertIn("query", response_data)
        self.assertIn("result", response_data)

        # Verify content
        self.assertEqual(response_data["query"], "What is ROS and what is it used for?")
        self.assertIsInstance(response_data["result"], str)
        self.assertGreater(len(response_data["result"]), 0)

    def test_rerank_qa_endpoint_service_error(self):
        # Arrange
        self.mock_rerank_service.answer_question.side_effect = Exception("Rerank service error")

        payload = {"query": "test query", "k_results": 4}

        # Act
        response = self.client.post("/rag-docs/api/v1/qa_ranked", json=payload)

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIn("detail", response.json())


if __name__ == "__main__":
    unittest.main()
