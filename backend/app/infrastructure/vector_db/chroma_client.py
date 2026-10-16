from typing import Any

import chromadb
from chromadb.api import ClientAPI

from app.core.config import Settings
from app.infrastructure.vector_db.scoring import COSINE_SPACE
from app.utils.logger import logger


COLLECTION_METADATA: dict[str, str] = {"hnsw:space": COSINE_SPACE}


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

    @staticmethod
    def _effective_space(collection: Any) -> str:
        """Read the collection's distance space; Chroma defaults to l2 when none was given.

        Order: metadata first (server 1.0.0 always reports l2 in its configuration, even for a
        cosine collection), then `configuration_json["hnsw"]` (1.0.12 bindings), then
        `configuration_json["hnsw_configuration"]` (server 1.0.0), else l2.
        """
        metadata = getattr(collection, "metadata", None) or {}
        if isinstance(metadata, dict) and metadata.get("hnsw:space"):
            return str(metadata["hnsw:space"])
        config = getattr(collection, "configuration_json", None) or {}
        for key in ("hnsw", "hnsw_configuration"):
            section = config.get(key) if isinstance(config, dict) else None
            if isinstance(section, dict) and section.get("space"):
                return str(section["space"])
        return "l2"

    def get_or_create_collection(self, name: str) -> None:
        """Ensure a cosine collection exists; refuse (never modify) an existing non-cosine one."""
        try:
            collection = self._client.get_collection(name=name)
        except Exception as e:
            logger.warning(f"Collection '{name}' not found: {e}")
            self._client.create_collection(name=name, metadata=COLLECTION_METADATA)
            logger.info(f"Collection '{name}' created")
            return

        space = self._effective_space(collection)
        if space != COSINE_SPACE:
            message = (
                f"Collection '{name}' uses space '{space}', but cosine is required. "
                "Chroma cannot change a collection's space: recreate the collection "
                "and re-ingest the documents."
            )
            logger.error(message)
            raise RuntimeError(message)
        logger.info(f"Collection '{name}' exists")
