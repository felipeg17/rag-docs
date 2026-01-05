from typing import Any
from uuid import UUID

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
    ) -> None:
        """Log a search interaction."""
        try:
            # Calculate metrics from results
            results_count = len(results)
            avg_score = self._calculate_avg_score(results) if results else None

            self._search_repo.log_search(
                document_id=document_id,
                query_text=query_text,
                k_results=k_results,
                results_count=results_count,
                avg_similarity_score=avg_score,
                execution_time_ms=execution_time_ms,
            )

            logger.debug(f"Logged search interaction for document {document_id}")
        except Exception as e:
            logger.error(f"Failed to log search interaction: {e}")

    def log_qa(
        self,
        document_id: UUID,
        question: str,
        answer: str,
        strategy: str,
        k_results: int,
        llm_model: str | None = None,
        execution_time_ms: int | None = None,
    ) -> None:
        """Log a Q&A interaction."""
        try:
            self._qa_repo.log_qa(
                document_id=document_id,
                question=question,
                answer=answer,
                strategy=strategy,
                k_results=k_results,
                llm_model=llm_model,
                execution_time_ms=execution_time_ms,
            )

            logger.debug(f"Logged Q&A interaction for document {document_id}")
        except Exception as e:
            logger.error(f"Failed to log Q&A interaction: {e}")

    @staticmethod
    def _calculate_avg_score(results: list[tuple[Any, float]]) -> float:
        """Calculate average similarity score from results."""
        if not results:
            return 0.0
        scores = [score for _, score in results]
        return sum(scores) / len(scores) if scores else 0.0
