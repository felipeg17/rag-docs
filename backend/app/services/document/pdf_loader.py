import base64

# TODO: Check the most recent way of use PyMUPDF
# #! https://pymupdf.readthedocs.io/en/latest/tutorial.html
import fitz  # type: ignore

from app.utils.logger import logger


class PDFLoader:
    @classmethod
    def load_from_base64(cls, base64_string: str) -> fitz.Document:
        """
        Decode base64 string and load PDF document.

        Args:
            base64_string: Base64-encoded PDF content

        Returns:
            PyMuPDF Document object

        Raises:
            ValueError: If base64 decoding or PDF loading fails
        """
        try:
            # Decode base64 to bytes
            pdf_bytes = base64.b64decode(base64_string)
            logger.info(f"Decoded PDF: {len(pdf_bytes)} bytes")

            # Load PDF with PyMuPDF
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            logger.info(f"PDF loaded: {pdf_document.page_count} pages")

            return pdf_document

        except Exception as e:
            logger.error(f"Failed to load PDF: {e}")
            raise ValueError(f"Invalid PDF data: {e}")
