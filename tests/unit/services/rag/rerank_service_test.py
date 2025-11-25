import json
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from app.core.config import Settings
from app.services.rag.rerank_service import RerankService


class TestRerankService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures_path = Path(__file__).parent.parent.parent.parent / "fixtures"
        golden_responses_path = fixtures_path / "golden_responses"

        # Load golden response
        with open(golden_responses_path / "rerank_qa_complete_response.json", "r") as f:
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
            default_rerank_top_n=self.settings_snapshot["default_rerank_top_n"],
            cohere_model=self.settings_snapshot["cohere_model"],
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
        self.service = RerankService(
            self.settings,
            self.mock_llm_client,
            self.mock_vdb_repo,
        )

    @patch("app.services.rag.rerank_service.StrOutputParser")
    @patch("app.services.rag.rerank_service.RunnableParallel")
    @patch("app.services.rag.rerank_service.ChatPromptTemplate.from_template")
    @patch("app.services.rag.rerank_service.ContextualCompressionRetriever")
    @patch("app.services.rag.rerank_service.CohereRerank")
    def test_answer_question_with_golden_response(
        self,
        mock_cohere_rerank,
        mock_compression_retriever,
        mock_chat_prompt,
        mock_runnable_parallel,
        mock_str_parser,
    ):
        """Test rerank QA service returns expected answer using golden response."""
        query = self.golden_response["input"]["query"]
        document_type = "documento-pdf"
        expected_answer = self.golden_response["response"]["content"]

        # Mock components
        mock_cohere_rerank.return_value = MagicMock()
        mock_compression_retriever.return_value = MagicMock()
        mock_chat_prompt.return_value = MagicMock()
        mock_str_parser.return_value = MagicMock()

        # Mock the LCEL chain to return expected answer
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = expected_answer

        # Mock RunnableParallel to return a chain that produces the expected result
        mock_setup = MagicMock()
        mock_setup.__or__.return_value.__or__.return_value.__or__.return_value = mock_chain
        mock_runnable_parallel.return_value = mock_setup

        # Act
        result = self.service.answer_question(query, document_type)

        # Assert
        self.assertEqual(result, expected_answer)
        mock_chain.invoke.assert_called_once_with(query)

    @patch("app.services.rag.rerank_service.StrOutputParser")
    @patch("app.services.rag.rerank_service.RunnableParallel")
    @patch("app.services.rag.rerank_service.ChatPromptTemplate.from_template")
    @patch("app.services.rag.rerank_service.ContextualCompressionRetriever")
    @patch("app.services.rag.rerank_service.CohereRerank")
    def test_answer_question_creates_cohere_reranker(
        self,
        mock_cohere_rerank,
        mock_compression_retriever,
        mock_chat_prompt,
        mock_runnable_parallel,
        mock_str_parser,
    ):
        """Test that Cohere reranker is created with correct parameters."""
        query = "What is ROS?"
        document_type = "documento-pdf"

        # Mock components
        mock_cohere_rerank.return_value = MagicMock()
        mock_compression_retriever.return_value = MagicMock()
        mock_chat_prompt.return_value = MagicMock()
        mock_str_parser.return_value = MagicMock()

        # Mock chain
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "Test answer"
        mock_setup = MagicMock()
        mock_setup.__or__.return_value.__or__.return_value.__or__.return_value = mock_chain
        mock_runnable_parallel.return_value = mock_setup

        # Act
        self.service.answer_question(query, document_type)

        # Assert
        mock_cohere_rerank.assert_called_once()
        call_kwargs = mock_cohere_rerank.call_args[1]
        self.assertEqual(call_kwargs["top_n"], self.settings.default_rerank_top_n)
        self.assertEqual(call_kwargs["model"], self.settings.cohere_model)


if __name__ == "__main__":
    unittest.main()
