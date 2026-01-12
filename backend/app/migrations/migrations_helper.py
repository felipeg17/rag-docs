import time
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.utils.logger import logger


def run_migrations(max_retries: int = 3, retry_delay: int = 2) -> None:
    """
    Run Alembic migrations to upgrade database to latest schema.

    This function is designed to be called during application startup.
    It handles concurrent pod startup by retrying on lock conflicts.

    Args:
        max_retries: Maximum number of retry attempts if migration fails
        retry_delay: Seconds to wait between retry attempts

    Raises:
        RuntimeError: If migrations fail after all retries
    """
    # Get alembic.ini path (should be in backend root)
    alembic_ini_path = Path(__file__).parent.parent.parent / "alembic.ini"

    if not alembic_ini_path.exists():
        raise FileNotFoundError(
            f"alembic.ini not found at {alembic_ini_path}. Ensure Alembic is properly initialized."
        )

    # Configure Alembic
    alembic_cfg = Config(str(alembic_ini_path))

    # Run migrations with retry logic
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Running database migrations (attempt {attempt}/{max_retries})...")
            command.upgrade(alembic_cfg, "head")
            logger.info("Database migrations completed successfully")
            return  # Success - exit function

        except Exception as e:
            error_msg = str(e).lower()

            # Check if error is due to concurrent migration (lock conflict)
            if "lock" in error_msg or "concurrent" in error_msg:
                if attempt < max_retries:
                    logger.warning(
                        f"Migration locked by another process. "
                        f"Retrying in {retry_delay}s... ({attempt}/{max_retries})"
                    )
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error("Failed to acquire migration lock after all retries")
                    raise RuntimeError(
                        "Database migration failed: lock conflict. "
                        "Another pod may be running migrations."
                    ) from e

            # For other errors, fail immediately
            logger.error(f"Database migration failed: {e}")
            raise RuntimeError(f"Database migration failed: {e}") from e

    # Should never reach here, but just in case
    raise RuntimeError("Database migration failed after all retries")
