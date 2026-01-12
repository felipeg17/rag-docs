from typing import Sequence

from langchain_postgres import ColumnDict
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.core.config import Settings
from app.utils.logger import logger


class PGVectorClient:
    # Standard metadata columns for RAG documents
    METADATA_COLUMNS: Sequence[ColumnDict] = [
        ColumnDict(name="titulo", data_type="TEXT", nullable=True),
        ColumnDict(name="tipo_documento", data_type="TEXT", nullable=True),
        ColumnDict(name="pagina", data_type="INTEGER", nullable=True),
        ColumnDict(name="fuente", data_type="TEXT", nullable=True),
    ]

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

        self._connection_string = (
            f"postgresql+psycopg://{settings.pgvector_user}:{settings.pgvector_password}"
            f"@{settings.pgvector_host}:{settings.pgvector_port}"
            f"/{settings.pgvector_database}"
        )
        self._engine: Engine = create_engine(
            self._connection_string,
            pool_pre_ping=True,
        )

    @property
    def connection_string(self) -> str:
        return self._connection_string

    @property
    def table_name(self) -> str:
        return self._settings.pgvector_table

    @property
    def schema_name(self) -> str:
        return self._settings.pgvector_schema

    def heartbeat(self) -> bool:
        """Check PostgreSQL connection health."""
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"PGVector heartbeat failed: {e}")
            return False

    def dispose(self) -> None:
        self._engine.dispose()
        logger.info("PGVector engine disposed")
