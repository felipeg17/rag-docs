from typing import Any
from uuid import UUID

from app.infrastructure.database.models import QAInteraction, SearchInteraction
from app.infrastructure.database.repositories.interaction_repository import (
    QAInteractionRepository,
    SearchInteractionRepository,
)
from app.utils.logger import logger


class InteractionService:
    """Service for logging search and Q&A interactions."""

    def __init__(
        self,
        search_repo: SearchInteractionRepository,
        qa_repo: QAInteractionRepository,
    ):
        self._search_repo = search_repo
        self._qa_repo = qa_repo

    def log_search(
        self,
        document_id: UUID,
        query_text: str,
        results: list[Any],  # Search results (tuples of Document, score)
        k_results: int,
        execution_time_ms: int | None = None,
    ) -> SearchInteraction | None:
        """Log a search interaction."""
        try:
            # Calculate metrics from results
            results_count = len(results)
            avg_score = self._calculate_avg_score(results) if results else None

            search_interaction = self._search_repo.log_search(
                document_id=document_id,
                query_text=query_text,
                k_results=k_results,
                results_count=results_count,
                avg_similarity_score=avg_score,
                execution_time_ms=execution_time_ms,
            )

            logger.info(
                f"Logged search interaction {search_interaction.id} for document {document_id}"
            )
            return search_interaction
        except Exception as e:
            logger.error(f"Failed to log search interaction: {e}")
            return None

    def log_qa(
        self,
        document_id: UUID,
        question: str,
        answer: str,
        strategy: str,
        k_results: int,
        llm_model: str | None = None,
        execution_time_ms: int | None = None,
    ) -> QAInteraction | None:
        """Log a Q&A interaction."""
        try:
            qa_interaction = self._qa_repo.log_qa(
                document_id=document_id,
                question=question,
                answer=answer,
                strategy=strategy,
                k_results=k_results,
                llm_model=llm_model,
                execution_time_ms=execution_time_ms,
            )

            logger.info(f"Logged Q&A interaction {qa_interaction.id} for document {document_id}")
            return qa_interaction
        except Exception as e:
            logger.error(f"Failed to log Q&A interaction: {e}")
            return None

    @staticmethod
    def _calculate_avg_score(results: list[tuple[Any, float]]) -> float:
        """Calculate average similarity score from results."""
        if not results:
            return 0.0
        scores = [score for _, score in results]
        return sum(scores) / len(scores) if scores else 0.0
