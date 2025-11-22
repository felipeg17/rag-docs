from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for proper resource management.
    """
    logger.info("Starting up RAG-docs application...")
    logger.info(f"Environment: {settings.chromadb_host}:{settings.chromadb_port}")

    # TODO Phase 2: Initialize infrastructure clients
    # chroma_client = get_chroma_client()
    # await chroma_client.healthcheck()

    logger.info("Application startup complete")

    yield  # Application runs here

    logger.info("Shutting down RAG-docs application...")

    # TODO Phase 2: Close connections gracefully
    # await chroma_client.close()

    logger.info("Application shutdown complete")
