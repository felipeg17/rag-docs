from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.utils.logger import logger


class DatabaseClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

        self._connection_string = (
            f"postgresql+psycopg://{settings.pgvector_user}:{settings.pgvector_password}"
            f"@{settings.pgvector_host}:{settings.pgvector_port}"
            f"/{settings.pgvector_database}"
        )

        # Create sync engine
        self._engine: Engine = create_engine(
            self._connection_string,
            pool_pre_ping=True,
            pool_size=5,  # Conservative for shared DB
            max_overflow=10,
        )

        # Session factory
        self._session_factory = sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
        )

        logger.info(
            f"Database client initialized: {settings.pgvector_host}:"
            f"{settings.pgvector_port}/{settings.pgvector_database}"
        )

    @property
    def engine(self) -> Engine:
        """Get SQLAlchemy engine."""
        return self._engine

    def get_session(self) -> Session:
        """Get new database session."""
        return self._session_factory()

    def heartbeat(self) -> bool:
        """Check database connection health."""
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database heartbeat failed: {e}")
            return False

    def dispose(self) -> None:
        """Dispose database engine."""
        self._engine.dispose()
        logger.info("Database engine disposed")
