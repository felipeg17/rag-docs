import unittest
from unittest.mock import MagicMock, patch

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.services.ingest.ingestion import DocumentIngestionService


class TestDocumentIngestionService(unittest.TestCase):
    def setUp(self):
        # Mock VectorDBRepository
        self.mock_vdb_repo = MagicMock()
        self.mock_vdb_repo.check_document_exists.return_value = False
        self.mock_vdb_repo.add_documents.return_value = ["id1", "id2"]

        # Mock TextSplitterFactory
        self.mock_splitter_factory = MagicMock()

        # Mock the splitter that factory returns
        self.mock_splitter = MagicMock()
        self.mock_splitter.split_documents.return_value = [
            Document(page_content="Chunk 1", metadata={"titulo": "test", "pagina": 0}),
            Document(page_content="Chunk 2", metadata={"titulo": "test", "pagina": 0}),
        ]
        self.mock_splitter_factory.create_splitter.return_value = self.mock_splitter

        # Create service instance
        self.service = DocumentIngestionService(
            self.mock_vdb_repo,
            self.mock_splitter_factory,
        )

    @patch("app.services.ingest.ingestion.PDFTextExtractor.extract_with_metadata")
    @patch("app.services.ingest.ingestion.PDFLoader.load_from_base64")
    def test_ingest_document_success(self, mock_pdf_loader, mock_text_extractor):
        # Arrange
        mock_pdf_document = MagicMock()
        mock_pdf_document.page_count = 2
        mock_pdf_loader.return_value = mock_pdf_document

        mock_documents = [
            Document(page_content="Page 1", metadata={"titulo": "test", "pagina": 0}),
            Document(page_content="Page 2", metadata={"titulo": "test", "pagina": 1}),
        ]
        mock_text_extractor.return_value = mock_documents

        # Act
        result = self.service.ingest_document(
            base64_content="fake_base64_content",
            title="test_document",
            document_type="documento-pdf",
            splitting_method="recursive",
        )

        # Assert
        self.assertTrue(result)

        # Verify all steps were called in order
        self.mock_vdb_repo.check_document_exists.assert_called_once_with(
            {"titulo": "test_document"}
        )
        mock_pdf_loader.assert_called_once_with("fake_base64_content")
        mock_text_extractor.assert_called_once_with(
            pdf_document=mock_pdf_document,
            title="test_document",
            document_type="documento-pdf",
        )
        self.mock_splitter_factory.create_splitter.assert_called_once_with(
            method="recursive",
            chunk_size=None,
            chunk_overlap=None,
        )
        self.mock_splitter.split_documents.assert_called_once_with(mock_documents)
        self.mock_vdb_repo.add_documents.assert_called_once()

    @patch("app.services.ingest.ingestion.PDFTextExtractor.extract_with_metadata")
    @patch("app.services.ingest.ingestion.PDFLoader.load_from_base64")
    def test_ingest_document_already_exists_returns_false(
        self, mock_pdf_loader, mock_text_extractor
    ):
        # Arrange - document already exists
        self.mock_vdb_repo.check_document_exists.return_value = True

        # Act
        result = self.service.ingest_document(
            base64_content="fake_base64_content",
            title="existing_document",
        )

        # Assert
        self.assertFalse(result)

        # Verify only check_document_exists was called, nothing else
        self.mock_vdb_repo.check_document_exists.assert_called_once_with(
            {"titulo": "existing_document"}
        )
        mock_pdf_loader.assert_not_called()
        mock_text_extractor.assert_not_called()
        self.mock_splitter_factory.create_splitter.assert_not_called()
        self.mock_vdb_repo.add_documents.assert_not_called()

    @patch("app.services.ingest.ingestion.PDFTextExtractor.extract_with_metadata")
    @patch("app.services.ingest.ingestion.PDFLoader.load_from_base64")
    def test_ingest_document_with_custom_chunk_parameters(
        self, mock_pdf_loader, mock_text_extractor
    ):
        """Test ingestion with custom chunk_size and chunk_overlap."""
        # Arrange
        mock_pdf_document = MagicMock()
        mock_pdf_loader.return_value = mock_pdf_document

        mock_documents = [Document(page_content="Test", metadata={})]
        mock_text_extractor.return_value = mock_documents

        custom_chunk_size = 1000
        custom_chunk_overlap = 100

        # Act
        result = self.service.ingest_document(
            base64_content="fake_base64",
            title="test",
            chunk_size=custom_chunk_size,
            chunk_overlap=custom_chunk_overlap,
        )

        # Assert
        self.assertTrue(result)
        self.mock_splitter_factory.create_splitter.assert_called_once_with(
            method="recursive",
            chunk_size=custom_chunk_size,
            chunk_overlap=custom_chunk_overlap,
        )

    @patch("app.services.ingest.ingestion.PDFTextExtractor.extract_with_metadata")
    @patch("app.services.ingest.ingestion.PDFLoader.load_from_base64")
    def test_ingest_document_with_semantic_splitting(self, mock_pdf_loader, mock_text_extractor):
        """Test ingestion with semantic splitting method."""
        # Arrange
        mock_pdf_document = MagicMock()
        mock_pdf_loader.return_value = mock_pdf_document

        mock_documents = [Document(page_content="Test", metadata={})]
        mock_text_extractor.return_value = mock_documents

        # Act
        result = self.service.ingest_document(
            base64_content="fake_base64",
            title="test",
            splitting_method="semantic",
        )

        # Assert
        self.assertTrue(result)
        self.mock_splitter_factory.create_splitter.assert_called_once_with(
            method="semantic",
            chunk_size=None,
            chunk_overlap=None,
        )

    @patch("app.services.ingest.ingestion.PDFTextExtractor.extract_with_metadata")
    @patch("app.services.ingest.ingestion.PDFLoader.load_from_base64")
    def test_ingest_document_with_recursive_splitter(self, mock_pdf_loader, mock_text_extractor):
        # Arrange
        mock_pdf_document = MagicMock()
        mock_pdf_loader.return_value = mock_pdf_document

        # Create a document with content long enough to be split
        long_content = "This is a test sentence. " * 100
        mock_documents = [
            Document(
                page_content=long_content,
                metadata={"titulo": "test_doc", "pagina": 0},
            )
        ]
        mock_text_extractor.return_value = mock_documents

        # Use REAL text splitter factory that returns real splitter
        real_splitter_factory = MagicMock()
        real_splitter = RecursiveCharacterTextSplitter(
            chunk_size=100,
            chunk_overlap=20,
        )
        real_splitter_factory.create_splitter.return_value = real_splitter

        # Create service with real splitter factory
        service = DocumentIngestionService(
            self.mock_vdb_repo,
            real_splitter_factory,
        )

        # Act
        result = service.ingest_document(
            base64_content="fake_base64",
            title="test_doc",
            chunk_size=100,
            chunk_overlap=20,
        )

        # Assert
        self.assertTrue(result)

        real_splitter_factory.create_splitter.assert_called_once_with(
            method="recursive",
            chunk_size=100,
            chunk_overlap=20,
        )

        # Verify actual splitting happened - should have multiple chunks
        self.mock_vdb_repo.add_documents.assert_called_once()
        actual_chunks = self.mock_vdb_repo.add_documents.call_args[0][0]

        # Verify chunks were actually created by the real splitter
        self.assertGreater(
            len(actual_chunks),
            25,
            "Should split into at least 25 chunks for 2500 characters with chunk size 100",
        )

        # Verify each chunk has the original metadata
        for chunk in actual_chunks:
            self.assertIsInstance(chunk, Document)
            self.assertEqual(chunk.metadata["titulo"], "test_doc")
            self.assertEqual(chunk.metadata["pagina"], 0)

        # Verify chunks respect size constraints (with some tolerance)
        for chunk in actual_chunks:
            self.assertLessEqual(
                len(chunk.page_content),
                150,
                f"Chunk too large: {len(chunk.page_content)} chars",
            )


if __name__ == "__main__":
    unittest.main()
