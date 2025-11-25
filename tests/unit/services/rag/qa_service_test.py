import json
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from langchain.schema import Document

from app.core.config import Settings
from app.services.rag.qa_service import QAService


class TestQAService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures_path = Path(__file__).parent.parent.parent.parent / "fixtures"
        golden_responses_path = fixtures_path / "golden_responses"

        # Load golden response
        with open(golden_responses_path / "llm_qa_response.json", "r") as f:
            cls.golden_response = json.load(f)

        # Load settings snapshot
        with open(golden_responses_path / "settings_snapshot.json", "r") as f:
            cls.settings_snapshot = json.load(f)["settings"]

    def setUp(self):
        # Use settings from golden response snapshot
        self.settings = Settings(
            openai_model=self.settings_snapshot["openai_model"],
            openai_temperature=self.settings_snapshot["openai_temperature"],
            openai_max_tokens=self.settings_snapshot["openai_max_tokens"],
            openai_top_p=self.settings_snapshot["openai_top_p"],
            default_k_results=self.settings_snapshot["default_k_results"],
            default_chunk_size=self.settings_snapshot["default_chunk_size"],
            default_chunk_overlap=self.settings_snapshot["default_chunk_overlap"],
        )

        # Mock LLMClient
        self.mock_llm_client = MagicMock()
        self.mock_llm = MagicMock()
        self.mock_llm_client.client = self.mock_llm

        # Mock VectorDBRepository
        self.mock_vdb_repo = MagicMock()
        self.mock_retriever = MagicMock()
        self.mock_vdb_repo.as_retriever.return_value = self.mock_retriever

        # Create service instance
        self.service = QAService(
            self.settings,
            self.mock_llm_client,
            self.mock_vdb_repo,
        )

    @patch("app.services.rag.qa_service.RetrievalQA.from_chain_type")
    @patch("app.services.rag.qa_service.PromptTemplate.from_template")
    def test_answer_question_with_golden_response(self, mock_prompt_template, mock_retrieval_qa):
        """Test QA service returns expected answer using golden response data."""
        # Arrange - Use golden response data
        query = self.golden_response["input"]["query"]
        document_type = "documento-pdf"

        # Convert golden response source documents to Langchain Documents
        source_docs = []
        for doc_data in self.golden_response["source_documents"]:
            doc = Document(
                page_content=doc_data["page_content"],
                metadata=doc_data["metadata"],
            )
            source_docs.append(doc)

        # Expected answer from golden response
        expected_answer = self.golden_response["response"]["content"]

        # Mock the QA chain to return golden response structure
        mock_qa_chain = MagicMock()
        mock_qa_chain.invoke.return_value = {
            "result": expected_answer,
            "source_documents": source_docs,
        }
        mock_retrieval_qa.return_value = mock_qa_chain

        mock_prompt = MagicMock()
        mock_prompt_template.return_value = mock_prompt

        # Act
        result = self.service.answer_question(query, document_type)

        # Assert - Verify result structure and content
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)
        self.assertIn("source_documents", result)

        # Verify answer content matches golden response
        self.assertEqual(result["result"], expected_answer)

        # Verify source documents are present
        self.assertEqual(len(result["source_documents"]), len(source_docs))
        self.assertIsInstance(result["source_documents"][0], Document)

        # Verify chain was invoked with correct query
        mock_qa_chain.invoke.assert_called_once_with({"query": query})

    @patch("app.services.rag.qa_service.RetrievalQA.from_chain_type")
    @patch("app.services.rag.qa_service.PromptTemplate.from_template")
    def test_answer_question_returns_source_documents(
        self, mock_prompt_template, mock_retrieval_qa
    ):
        """Test that answer includes source documents with metadata."""
        # Arrange
        query = "What is ROS?"
        document_type = "documento-pdf"

        # Create mock source documents with metadata
        mock_doc1 = Document(
            page_content="ROS is a robotics framework",
            metadata={"titulo": "ros-intro", "pagina": 0, "tipo-documento": document_type},
        )
        mock_doc2 = Document(
            page_content="ROS provides tools for robotics",
            metadata={"titulo": "ros-intro", "pagina": 1, "tipo-documento": document_type},
        )

        mock_qa_chain = MagicMock()
        mock_qa_chain.invoke.return_value = {
            "result": "ROS is a robotics framework",
            "source_documents": [mock_doc1, mock_doc2],
        }
        mock_retrieval_qa.return_value = mock_qa_chain

        # Act
        result = self.service.answer_question(query, document_type)

        # Assert
        self.assertIn("source_documents", result)
        self.assertEqual(len(result["source_documents"]), 2)

        # Verify source documents have correct metadata
        for doc in result["source_documents"]:
            self.assertIsInstance(doc, Document)
            self.assertIn("titulo", doc.metadata)
            self.assertIn("pagina", doc.metadata)
            self.assertIn("tipo-documento", doc.metadata)


if __name__ == "__main__":
    unittest.main()
