import fitz  # type: ignore
from langchain.schema import Document

from app.utils.logger import logger


class PDFTextExtractor:
    """Extract text from PDF into langchain documents with metadata."""

    @classmethod
    def extract_with_metadata(
        cls,
        pdf_document: fitz.Document,
        title: str,
        document_type: str,
    ) -> list[Document]:
        """
        Extract text from each PDF page as Langchain Documents.

        Args:
            pdf_document: PyMuPDF Document object
            title: Document title for metadata
            document_type: Document type for metadata (e.g., "documento-pdf")

        Returns:
            List of Langchain Documents with page content and metadata
        """
        documents: list[Document] = []

        for page_number in range(pdf_document.page_count):
            logger.info(f"Processing page {page_number + 1}/{pdf_document.page_count}")

            # Extract text from page
            page: fitz.Page = pdf_document.load_page(page_number)
            # TODO:  Check why fitz.Page does not have `get_text`
            # * https://pymupdf.readthedocs.io/en/latest/page.html#Page.get_text
            page_text: str = page.get_text("text")

            # Create Langchain Document with metadata
            documents.append(
                Document(
                    page_content=page_text,
                    metadata={
                        "titulo": title,
                        "tipo_documento": document_type,
                        "pagina": page_number,
                    },
                )
            )

        logger.info(f"Extracted {len(documents)} pages from '{title}'")
        return documents
