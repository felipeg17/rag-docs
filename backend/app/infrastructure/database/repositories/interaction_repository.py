from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.database.models import QAInteraction, SearchInteraction
from app.infrastructure.database.repositories.base import BaseRepository


class SearchInteractionRepository(BaseRepository[SearchInteraction]):
    """Repository for search interaction logging."""

    def __init__(self, session: Session):
        super().__init__(session, SearchInteraction)

    def log_search(
        self,
        document_id: UUID,
        query_text: str,
        k_results: int | None = None,
        results_count: int | None = None,
        avg_similarity_score: float | None = None,
        execution_time_ms: int | None = None,
        session_id: UUID | None = None,
        user_id: str | None = None,
    ) -> SearchInteraction:
        """Log a search interaction."""
        return self.create(
            document_id=document_id,
            query_text=query_text,
            k_results=k_results,
            results_count=results_count,
            avg_similarity_score=avg_similarity_score,
            execution_time_ms=execution_time_ms,
            session_id=session_id,
            user_id=user_id,
        )


class QAInteractionRepository(BaseRepository[QAInteraction]):
    """Repository for Q&A interaction logging."""

    def __init__(self, session: Session):
        super().__init__(session, QAInteraction)

    def log_qa(
        self,
        document_id: UUID,
        question: str,
        answer: str,
        strategy: str | None = None,
        k_results: int | None = None,
        llm_model: str | None = None,
        embedding_model: str | None = None,
        execution_time_ms: int | None = None,
        tokens_used: int | None = None,
        session_id: UUID | None = None,
        user_id: str | None = None,
    ) -> QAInteraction:
        """Log a Q&A interaction."""
        return self.create(
            document_id=document_id,
            question=question,
            answer=answer,
            strategy=strategy,
            k_results=k_results,
            llm_model=llm_model,
            embedding_model=embedding_model,
            execution_time_ms=execution_time_ms,
            tokens_used=tokens_used,
            session_id=session_id,
            user_id=user_id,
        )

    def get_by_document_id(self, document_id: UUID) -> Sequence[QAInteraction]:
        """Retrieve all QA interactions for a specific document."""
        query = (
            select(QAInteraction)
            .where(QAInteraction.document_id == document_id)
            .order_by(QAInteraction.updated_at.desc())
        )
        return self._session.execute(query).scalars().all()
