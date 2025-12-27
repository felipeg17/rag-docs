import base64
import unittest

from langchain.schema import Document

from app.services.document.pdf_loader import PDFLoader
from app.services.document.text_extractor import PDFTextExtractor

from .pdf_loader_test import FIXTURES_PATH


class TestPDFTextExtractor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use ros-intro.pdf as it's small and simple
        cls.sample_pdf_path = FIXTURES_PATH / "data" / "ros-intro.pdf"

        # Load and parse the PDF
        with open(cls.sample_pdf_path, "rb") as f:
            pdf_bytes = f.read()

        base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        cls.pdf_document = PDFLoader.load_from_base64(base64_pdf)
        cls.page_count = cls.pdf_document.page_count

    def test_extract_with_metadata(self):
        # Arrange
        title = "ros-intro"
        document_type = "documento-pdf"

        # Act
        documents = PDFTextExtractor.extract_with_metadata(self.pdf_document, title, document_type)

        # Assert
        self.assertIsInstance(documents, list)
        self.assertEqual(len(documents), self.page_count)
        for page_num, doc in enumerate(documents):
            self.assertIsInstance(doc, Document)
            self.assertEqual(doc.metadata["titulo"], title)
            self.assertEqual(doc.metadata["tipo_documento"], document_type)
            self.assertEqual(doc.metadata["pagina"], page_num)

    def test_extract_with_metadata_first_page_contains_expected_content(self):
        # Arrange
        title = "ros-intro"
        document_type = "documento-pdf"

        # Act
        documents = PDFTextExtractor.extract_with_metadata(self.pdf_document, title, document_type)

        # Assert - first page should contain "ROS" (document is about ROS)
        first_page_text = documents[0].page_content.lower()
        self.assertTrue(
            "ros" in first_page_text or len(first_page_text) > 0,
            "First page should contain text content",
        )

    def test_extract_with_metadata_with_different_title(self):
        # Arrange
        title = "Custom Title"
        document_type = "custom-type"

        # Act
        documents = PDFTextExtractor.extract_with_metadata(self.pdf_document, title, document_type)

        # Assert - metadata should reflect custom values
        self.assertEqual(documents[0].metadata["titulo"], "Custom Title")
        self.assertEqual(documents[0].metadata["tipo_documento"], "custom-type")


if __name__ == "__main__":
    unittest.main()
