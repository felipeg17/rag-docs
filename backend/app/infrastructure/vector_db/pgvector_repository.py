from langchain.schema import Document
from langchain_postgres import PGEngine, PGVectorStore
from langchain_postgres.v2.indexes import DistanceStrategy

from app.core.config import Settings
from app.infrastructure.embeddings.client import EmbeddingsClient
from app.infrastructure.vector_db.pgvector_client import PGVectorClient
from app.infrastructure.vector_db.scoring import cosine_distance_to_similarity
from app.utils.logger import logger


class PGVectorDBRepository:
    """Repository for vector database operations using PGVector."""

    def __init__(
        self,
        settings: Settings,
        vectordb_client: PGVectorClient,
        embeddings_client: EmbeddingsClient,
    ) -> None:
        self._settings = settings
        self._vectordb_client = vectordb_client
        self._embeddings = embeddings_client.client

        # Initialize Langchain PGVector Engine
        self._engine = PGEngine.from_connection_string(
            url=vectordb_client.connection_string,
        )
        try:
            self._engine.init_vectorstore_table(
                table_name=self._settings.pgvector_table,
                schema_name=self._settings.pgvector_schema,
                vector_size=self._settings.get_vector_size(),
                metadata_columns=list(PGVectorClient.METADATA_COLUMNS),
            )
        except Exception as e:
            if "already exists" in str(e):
                logger.info(f"PGVector table '{self._settings.pgvector_table}' already exists")
            else:
                logger.error(f"Error initializing PGVector table: {e}")

        # Initialize Langchain PGVectorStore
        self._vdb = PGVectorStore.create_sync(
            engine=self._engine,
            table_name=self._settings.pgvector_table,
            schema_name=self._settings.pgvector_schema,
            embedding_service=self._embeddings,
            distance_strategy=DistanceStrategy.COSINE_DISTANCE,
            metadata_columns=[col["name"] for col in PGVectorClient.METADATA_COLUMNS],
        )

        logger.info(f"VectorDB repository initialized with table '{self._settings.pgvector_table}'")

    @property
    def vdb(self) -> PGVectorStore:
        """Get the Langchain PGVectorStore vector database."""
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
        where_document = where_document

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
        results = self._vdb.similarity_search(
            query="",
            k=1,
            filter=title_filter,
        )
        return len(results) > 0
