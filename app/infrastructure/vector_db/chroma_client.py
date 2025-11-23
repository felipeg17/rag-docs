import chromadb
from chromadb.api import ClientAPI

from app.core.config import Settings
from app.utils.logger import logger


class ChromaDBClient:
    """ChromaDB HTTP client wrapper."""

    def __init__(self, settings: Settings) -> None:
        self._client: ClientAPI = chromadb.HttpClient(
            host=f"http://{settings.chromadb_host}:{settings.chromadb_port}",
            tenant=settings.chromadb_tenant,
            database=settings.chromadb_database,
        )
        logger.info(
            f"ChromaDB client initialized: {settings.chromadb_host}:{settings.chromadb_port}"
        )

    @property
    def client(self) -> ClientAPI:
        return self._client

    def heartbeat(self) -> int:
        """Check ChromaDB connection health."""
        return self._client.heartbeat()

    def get_or_create_collection(self, name: str) -> None:
        """Ensure collection exists, create if needed."""
        try:
            self._client.get_collection(name=name)
            logger.info(f"Collection '{name}' exists")
        except Exception as e:
            logger.warning(f"Collection '{name}' not found: {e}")
            self._client.create_collection(name=name)
            logger.info(f"Collection '{name}' created")
