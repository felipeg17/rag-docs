import hashlib
from uuid import UUID

from app.infrastructure.database.models import Document
from app.infrastructure.database.repositories.document_repository import DocumentRepository
from app.utils.logger import logger


class DocumentService:
    """Service for document persistence operations."""

    def __init__(self, document_repo: DocumentRepository):
        self._doc_repo = document_repo

    def create_document(
        self,
        title: str,
        document_type: str,
        content: bytes,  # Raw PDF content for hashing
        file_size_bytes: int | None = None,
        page_count: int | None = None,
    ) -> Document:
        """
        Create new document record.

        Returns existing document if content hash matches (deduplication).
        """
        # Compute content hash for deduplication
        content_hash = self._compute_hash(content)

        # Check if document already exists
        existing_document = self._doc_repo.get_by_content_hash(content_hash)
        if existing_document:
            logger.info(
                f"Document with hash {content_hash[:8]}... already exists: {existing_document.id}"
            )
            return existing_document

        # Create new document
        document = self._doc_repo.create(
            title=title,
            document_type=document_type,
            content_hash=content_hash,
            file_size_bytes=file_size_bytes,
            page_count=page_count,
            status="active",
        )

        logger.info(f"Created document: {document.id} - {document.title}")
        return document

    def get_document(self, document_id: UUID) -> Document | None:
        """Get document by ID."""
        return self._doc_repo.get_by_id(document_id)

    def get_by_title(self, title: str) -> Document | None:
        """Get document by title."""
        return self._doc_repo.get_by_title(title)

    @staticmethod
    def _compute_hash(content: bytes) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content).hexdigest()
