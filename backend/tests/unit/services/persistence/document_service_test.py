import hashlib
import unittest
from unittest.mock import MagicMock
from uuid import uuid4

from app.infrastructure.database.models import Document
from app.services.persistence.document_service import DocumentService


class TestDocumentService(unittest.TestCase):
    def setUp(self):
        # Mock DocumentRepository
        self.mock_doc_repo = MagicMock()

        # Create service instance
        self.service = DocumentService(self.mock_doc_repo)

    def test_create_document_success(self):
        """Test creating a new document successfully."""
        # Arrange
        title = "test-document"
        document_type = "documento-pdf"
        content = b"Test PDF content"
        file_size = len(content)
        page_count = 5

        # Mock repository to return None (no existing document)
        self.mock_doc_repo.get_by_content_hash.return_value = None

        # Mock created document
        expected_doc = Document()
        expected_doc.id = uuid4()
        expected_doc.title = title
        expected_doc.document_type = document_type
        expected_doc.content_hash = hashlib.sha256(content).hexdigest()
        self.mock_doc_repo.create.return_value = expected_doc

        # Act
        result = self.service.create_document(
            title=title,
            document_type=document_type,
            content=content,
            file_size_bytes=file_size,
            page_count=page_count,
        )

        # Assert
        self.assertEqual(result, expected_doc)
        self.mock_doc_repo.get_by_content_hash.assert_called_once()
        self.mock_doc_repo.create.assert_called_once_with(
            title=title,
            document_type=document_type,
            content_hash=expected_doc.content_hash,
            file_size_bytes=file_size,
            page_count=page_count,
            status="active",
        )

    def test_create_document_deduplication(self):
        """Test that creating a document with existing hash returns existing document."""
        # Arrange
        title = "new-title"
        document_type = "documento-pdf"
        content = b"Duplicate content"

        # Mock existing document with same hash
        existing_doc = Document()
        existing_doc.id = uuid4()
        existing_doc.title = "old-title"
        existing_doc.content_hash = hashlib.sha256(content).hexdigest()

        self.mock_doc_repo.get_by_content_hash.return_value = existing_doc

        # Act
        result = self.service.create_document(
            title=title,
            document_type=document_type,
            content=content,
        )

        # Assert
        self.assertEqual(result, existing_doc)
        self.mock_doc_repo.get_by_content_hash.assert_called_once()
        # Should NOT create new document when hash exists
        self.mock_doc_repo.create.assert_not_called()

    def test_get_document_by_id_found(self):
        """Test retrieving document by ID when it exists."""
        # Arrange
        doc_id = uuid4()
        expected_doc = Document()
        expected_doc.id = doc_id
        expected_doc.title = "test-doc"

        self.mock_doc_repo.get_by_id.return_value = expected_doc

        # Act
        result = self.service.get_document(doc_id)

        # Assert
        self.assertEqual(result, expected_doc)
        self.mock_doc_repo.get_by_id.assert_called_once_with(doc_id)

    def test_get_document_by_id_not_found(self):
        """Test retrieving document by ID when it doesn't exist."""
        # Arrange
        doc_id = uuid4()
        self.mock_doc_repo.get_by_id.return_value = None

        # Act
        result = self.service.get_document(doc_id)

        # Assert
        self.assertIsNone(result)
        self.mock_doc_repo.get_by_id.assert_called_once_with(doc_id)

    def test_get_by_title_found(self):
        """Test retrieving document by title when it exists."""
        # Arrange
        title = "test-document"
        expected_doc = Document()
        expected_doc.id = uuid4()
        expected_doc.title = title

        self.mock_doc_repo.get_by_title.return_value = expected_doc

        # Act
        result = self.service.get_by_title(title)

        # Assert
        self.assertEqual(result, expected_doc)
        self.mock_doc_repo.get_by_title.assert_called_once_with(title)

    def test_get_by_title_not_found(self):
        """Test retrieving document by title when it doesn't exist."""
        # Arrange
        title = "nonexistent-doc"
        self.mock_doc_repo.get_by_title.return_value = None

        # Act
        result = self.service.get_by_title(title)

        # Assert
        self.assertIsNone(result)
        self.mock_doc_repo.get_by_title.assert_called_once_with(title)

    def test_compute_hash_generates_consistent_hash(self):
        """Test that _compute_hash generates consistent SHA-256 hashes."""
        # Arrange
        content1 = b"Test content for hashing"
        content2 = b"Test content for hashing"
        content3 = b"Different content"

        expected_hash1 = hashlib.sha256(content1).hexdigest()
        expected_hash3 = hashlib.sha256(content3).hexdigest()

        # Act
        hash1 = self.service._compute_hash(content1)
        hash2 = self.service._compute_hash(content2)
        hash3 = self.service._compute_hash(content3)

        # Assert
        self.assertEqual(hash1, expected_hash1)
        self.assertEqual(hash1, hash2, "Same content should produce same hash")
        self.assertNotEqual(hash1, hash3, "Different content should produce different hash")
        self.assertEqual(len(hash1), 64, "SHA-256 hash should be 64 hex characters")


if __name__ == "__main__":
    unittest.main()
