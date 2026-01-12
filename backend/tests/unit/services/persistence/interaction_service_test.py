import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.infrastructure.database.models import QAInteraction, SearchInteraction
from app.services.persistence.interaction_service import InteractionService


class TestInteractionService(unittest.TestCase):
    def setUp(self):
        # Mock repositories
        self.mock_search_repo = MagicMock()
        self.mock_qa_repo = MagicMock()

        # Create service instance
        self.service = InteractionService(
            search_repo=self.mock_search_repo,
            qa_repo=self.mock_qa_repo,
        )

    @patch("app.services.persistence.interaction_service.logger")
    def test_log_search_success(self, mock_logger):
        """Test logging a search interaction successfully."""
        # Arrange
        document_id = uuid4()
        query_text = "What is ROS?"
        k_results = 5
        execution_time_ms = 150

        # Mock search results (tuples of Document, score)
        mock_doc1 = MagicMock()
        mock_doc2 = MagicMock()
        results = [(mock_doc1, 0.9), (mock_doc2, 0.8)]

        # Mock created interaction
        expected_interaction = SearchInteraction()
        expected_interaction.id = uuid4()
        expected_interaction.document_id = document_id
        expected_interaction.query_text = query_text
        expected_interaction.k_results = k_results
        expected_interaction.results_count = 2
        expected_interaction.avg_similarity_score = 0.85
        expected_interaction.execution_time_ms = execution_time_ms

        self.mock_search_repo.log_search.return_value = expected_interaction

        # Act
        result = self.service.log_search(
            document_id=document_id,
            query_text=query_text,
            results=results,
            k_results=k_results,
            execution_time_ms=execution_time_ms,
        )

        # Assert
        self.assertEqual(result, expected_interaction)
        self.mock_search_repo.log_search.assert_called_once()

        # Verify call arguments (check float separately due to precision)
        call_args = self.mock_search_repo.log_search.call_args
        self.assertEqual(call_args.kwargs["document_id"], document_id)
        self.assertEqual(call_args.kwargs["query_text"], query_text)
        self.assertEqual(call_args.kwargs["k_results"], k_results)
        self.assertEqual(call_args.kwargs["results_count"], 2)
        self.assertAlmostEqual(call_args.kwargs["avg_similarity_score"], 0.85, places=2)
        self.assertEqual(call_args.kwargs["execution_time_ms"], execution_time_ms)

        mock_logger.info.assert_called_once()

    @patch("app.services.persistence.interaction_service.logger")
    def test_log_search_handles_exception(self, mock_logger):
        """Test that log_search handles exceptions gracefully."""
        # Arrange
        document_id = uuid4()
        query_text = "Test query"
        results = []
        k_results = 5

        # Mock repository to raise exception
        self.mock_search_repo.log_search.side_effect = Exception("Database error")

        # Act
        result = self.service.log_search(
            document_id=document_id,
            query_text=query_text,
            results=results,
            k_results=k_results,
        )

        # Assert
        self.assertIsNone(result)
        mock_logger.error.assert_called_once()

    @patch("app.services.persistence.interaction_service.logger")
    def test_log_qa_success(self, mock_logger):
        """Test logging a Q&A interaction successfully."""
        # Arrange
        document_id = uuid4()
        question = "What is ROS?"
        answer = "ROS is a robotics framework."
        strategy = "standard"
        k_results = 3
        llm_model = "gpt-4"
        execution_time_ms = 2000

        # Mock created interaction
        expected_interaction = QAInteraction()
        expected_interaction.id = uuid4()
        expected_interaction.document_id = document_id
        expected_interaction.question = question
        expected_interaction.answer = answer
        expected_interaction.strategy = strategy
        expected_interaction.k_results = k_results
        expected_interaction.llm_model = llm_model
        expected_interaction.execution_time_ms = execution_time_ms

        self.mock_qa_repo.log_qa.return_value = expected_interaction

        # Act
        result = self.service.log_qa(
            document_id=document_id,
            question=question,
            answer=answer,
            strategy=strategy,
            k_results=k_results,
            llm_model=llm_model,
            execution_time_ms=execution_time_ms,
        )

        # Assert
        self.assertEqual(result, expected_interaction)
        self.mock_qa_repo.log_qa.assert_called_once_with(
            document_id=document_id,
            question=question,
            answer=answer,
            strategy=strategy,
            k_results=k_results,
            llm_model=llm_model,
            execution_time_ms=execution_time_ms,
        )
        mock_logger.info.assert_called_once()

    @patch("app.services.persistence.interaction_service.logger")
    def test_log_qa_handles_exception(self, mock_logger):
        """Test that log_qa handles exceptions gracefully."""
        # Arrange
        document_id = uuid4()
        question = "Test question"
        answer = "Test answer"
        strategy = "standard"
        k_results = 3

        # Mock repository to raise exception
        self.mock_qa_repo.log_qa.side_effect = Exception("Database error")

        # Act
        result = self.service.log_qa(
            document_id=document_id,
            question=question,
            answer=answer,
            strategy=strategy,
            k_results=k_results,
        )

        # Assert
        self.assertIsNone(result)
        mock_logger.error.assert_called_once()

    def test_calculate_avg_score_with_results(self):
        """Test calculating average similarity score from results."""
        # Arrange
        mock_doc1 = MagicMock()
        mock_doc2 = MagicMock()
        mock_doc3 = MagicMock()
        results = [
            (mock_doc1, 2.0),
            (mock_doc2, 2.5),
            (mock_doc3, 1.5),
        ]

        # Act
        avg_score = self.service._calculate_avg_score(results)

        # Assert
        expected_avg = (2.0 + 2.5 + 1.5) / 3
        self.assertAlmostEqual(avg_score, expected_avg, places=2)

    def test_calculate_avg_score_empty_results(self):
        """Test calculating average score with empty results."""
        # Arrange
        results = []

        # Act
        avg_score = self.service._calculate_avg_score(results)

        # Assert
        self.assertEqual(avg_score, 0.0)

    def test_calculate_avg_score_single_result(self):
        """Test calculating average score with single result."""
        # Arrange
        mock_doc = MagicMock()
        results = [(mock_doc, 0.95)]

        # Act
        avg_score = self.service._calculate_avg_score(results)

        # Assert
        self.assertEqual(avg_score, 0.95)


if __name__ == "__main__":
    unittest.main()
