import base64
from pathlib import Path
import unittest

import fitz  # type: ignore[import-untyped]

from app.services.document.pdf_loader import PDFLoader


class TestPDFLoader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use ros-intro.pdf as it's small and simple
        project_root = Path(__file__).parent.parent.parent.parent.parent
        cls.sample_pdf_path = project_root / "documents" / "ros-intro.pdf"

        with open(cls.sample_pdf_path, "rb") as f:
            pdf_bytes = f.read()

        cls.valid_base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        cls.pdf_size = len(pdf_bytes)

    def test_load_from_base64_success(self):
        # Act
        pdf_document = PDFLoader.load_from_base64(self.valid_base64_pdf)

        # Assert
        self.assertIsInstance(pdf_document, fitz.Document)
        self.assertGreater(pdf_document.page_count, 0)
        self.assertIsNotNone(pdf_document)

    def test_load_from_base64_invalid_base64_raises_error(self):
        # Arrange
        invalid_base64 = "not-valid-base64"

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            PDFLoader.load_from_base64(invalid_base64)

        self.assertIn("Invalid PDF data", str(context.exception))

    def test_load_from_base64_empty_string_raises_error(self):
        # Arrange
        empty_string = ""

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            PDFLoader.load_from_base64(empty_string)

        self.assertIn("Invalid PDF data", str(context.exception))


if __name__ == "__main__":
    unittest.main()
