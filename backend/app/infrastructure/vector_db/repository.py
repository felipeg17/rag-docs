from langchain.schema import Document
from langchain_chroma import Chroma

from app.core.config import Settings
from app.infrastructure.embeddings.client import EmbeddingsClient
from app.infrastructure.vector_db.chroma_client import COLLECTION_METADATA, ChromaDBClient
from app.infrastructure.vector_db.scoring import cosine_distance_to_similarity
from app.utils.logger import logger


class VectorDBRepository:
    """Repository for vector database operations using ChromaDB."""

    def __init__(
        self,
        settings: Settings,
        chroma_client: ChromaDBClient,
        embeddings_client: EmbeddingsClient,
    ) -> None:
        self._settings = settings
        self._chroma_http_client = chroma_client.client
        self._embeddings = embeddings_client.client

        # Ensure collection exists
        chroma_client.get_or_create_collection(self._settings.chromadb_collection)

        # Initialize Langchain Chroma wrapper
        self._vdb = Chroma(
            collection_name=self._settings.chromadb_collection,
            embedding_function=self._embeddings,
            client=self._chroma_http_client,
            collection_metadata=COLLECTION_METADATA,
        )
        logger.info(
            f"VectorDB repository initialized with collection "
            f"'{self._settings.chromadb_collection}'"
        )

    @property
    def vdb(self) -> Chroma:
        """Get the Langchain Chroma vector database."""
        return self._vdb

    def add_documents(self, documents: list[Document]) -> list[str]:
        return self._vdb.add_documents(documents)

    def similarity_search_with_score(
        self,
        query: str,
        k: int | None = None,
        metadata_filter: dict | None = None,
        where_document: dict | None = None,
    ) -> list[tuple[Document, float]]:
        """Perform similarity search with scores."""
        # * Caller-supplied filter is never replaced; default only when None
        filter = {"tipo_documento": "documento-pdf"} if metadata_filter is None else metadata_filter
        # * Search for documents that at least have one space in their content
        # TODO: Check how to avoid this default
        where_document = where_document or {"$contains": " "}

        return self._vdb.similarity_search_with_score(
            query=query,
            k=k or self._settings.default_k_results,
            filter=filter,
            where_document=where_document,
        )

    def similarity_search_with_relevance_scores(
        self,
        query: str,
        k: int | None = None,
        metadata_filter: dict | None = None,
        where_document: dict | None = None,
    ) -> list[tuple[Document, float]]:
        """Similarity search with scores as cosine similarity in [0, 1] (higher is better)."""
        return [
            (doc, cosine_distance_to_similarity(distance))
            for doc, distance in self.similarity_search_with_score(
                query=query,
                k=k,
                metadata_filter=metadata_filter,
                where_document=where_document,
            )
        ]

    def as_retriever(self, search_type: str = "similarity", search_kwargs: dict | None = None):
        """Get retriever for RAG chains."""
        return self._vdb.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs or {},
        )

    def check_document_exists(self, title_filter: dict) -> bool:
        """Check if document exists by metadata filter."""
        # * Check if a document exist with the given title
        # TODO: Same document can be ingested multiple times using different names
        results = self._vdb.get(where=title_filter)
        return len(results.get("ids", [])) > 0
