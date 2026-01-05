from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.database.models import Document
from app.infrastructure.database.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Repository for document operations."""

    def __init__(self, session: Session):
        super().__init__(session, Document)

    def get_by_title(self, title: str) -> Document | None:
        """Get document by exact title."""
        query = select(Document).where(Document.title == title)
        return self._session.execute(query).scalar_one_or_none()

    def get_by_content_hash(self, content_hash: str) -> Document | None:
        """Get document by content hash."""
        query = select(Document).where(Document.content_hash == content_hash)
        return self._session.execute(query).scalar_one_or_none()
