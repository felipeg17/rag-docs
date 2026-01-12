from app.infrastructure.vector_db.repository import VectorDBRepository
from app.services.document.pdf_loader import PDFLoader
from app.services.document.text_extractor import PDFTextExtractor
from app.services.document.text_splitter import TextSplitterFactory
from app.utils.logger import logger


class DocumentIngestionService:
    """Service for ingesting PDF documents into vector database."""

    def __init__(
        self,
        vdb_repository: VectorDBRepository,
        splitter_factory: TextSplitterFactory,
    ) -> None:
        self._vdb_repo = vdb_repository
        self._splitter_factory = splitter_factory

    def ingest_document(
        self,
        base64_content: str,
        title: str,
        document_type: str = "documento_pdf",
        splitting_method: str = "recursive",
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> bool:
        """
        Ingest PDF document into vector database.

        Args:
            base64_content: Base64-encoded PDF
            title: Document title
            document_type: Document type for metadata
            splitting_method: "semantic" or "recursive"
            chunk_size: Optional chunk size (uses default if None)
            chunk_overlap: Optional chunk overlap (uses default if None)

        Returns:
            True if ingested, False if already exists
        """
        # 1. Check if document already exists
        if self._vdb_repo.check_document_exists({"titulo": title}):
            logger.info(f"Document '{title}' already exists in VDB")
            return False

        # 2. Load PDF from base64
        pdf_document = PDFLoader.load_from_base64(base64_content)

        # 3. Extract text with metadata
        documents = PDFTextExtractor.extract_with_metadata(
            pdf_document=pdf_document,
            title=title,
            document_type=document_type,
        )

        # 4. Create text splitter
        splitter = self._splitter_factory.create_splitter(
            method=splitting_method,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        # 5. Split documents into chunks
        chunks = splitter.split_documents(documents)
        logger.info(f"Split into {len(chunks)} chunks")

        # 6. Add to vector database
        self._vdb_repo.add_documents(chunks)
        logger.info(f"Document '{title}' ingested successfully")

        return True
