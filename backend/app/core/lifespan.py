from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import VectorDBType, settings
from app.core.dependencies import (
    get_chroma_client,
    get_embeddings_client,
    get_llm_client,
    get_pgvector_client,
)
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for proper resource management.
    """
    logger.info("Starting up RAG-docs application...")

    # Verify vector database connection based on config
    if settings.vector_db_type == VectorDBType.PGVECTOR:
        pgvector_client = get_pgvector_client()
        logger.info(f"PGVector heartbeat: {pgvector_client.heartbeat()}")
    else:
        chroma_client = get_chroma_client()
        logger.info(f"ChromaDB heartbeat: {chroma_client.heartbeat()}")

    # Verify llm model
    llm_client = get_llm_client()
    logger.info(f"LLM model: {llm_client.llm_model}")

    # Verify embeddings model
    embeddings_client = get_embeddings_client()
    logger.info(f"Embeddings model: {embeddings_client.embeddings_model}")

    logger.info("Application startup complete")

    yield  # Application runs here

    logger.info("Shutting down RAG-docs application...")
