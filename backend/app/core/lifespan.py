from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.dependencies import get_chroma_client, get_embeddings_client, get_llm_client
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for proper resource management.
    """
    logger.info("Starting up RAG-docs application...")

    # Verify ChromaDB connection
    chroma_client = get_chroma_client()
    heartbeat = chroma_client.heartbeat()
    logger.info(f"ChromaDB heartbeat: {heartbeat}")

    # Verify llm model
    llm_client = get_llm_client()
    logger.info(f"LLM model: {llm_client.llm_model}")

    # Verify embeddings model
    embeddings_client = get_embeddings_client()
    logger.info(f"Embeddings model: {embeddings_client.embeddings_model}")

    logger.info("Application startup complete")

    yield  # Application runs here

    logger.info("Shutting down RAG-docs application...")
