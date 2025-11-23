from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, settings
from app.infrastructure.embeddings.client import EmbeddingsClient
from app.infrastructure.llm.client import LLMClient
from app.infrastructure.vector_db.chroma_client import ChromaDBClient
from app.infrastructure.vector_db.repository import VectorDBRepository
from app.services.document.text_splitter import TextSplitterFactory
from app.services.ingest.ingestion import DocumentIngestionService
from app.services.rag.qa_service import QAService
from app.services.rag.rerank_service import RerankService


# ============================================================================
# Configuration Dependency
# ============================================================================
def get_settings() -> Settings:
    return settings


SettingsDep = Annotated[Settings, Depends(get_settings)]


# ============================================================================
# Infrastructure Dependencies
# ============================================================================
@lru_cache()
def get_llm_client() -> LLMClient:
    """Get LLM client"""
    return LLMClient(settings)


@lru_cache()
def get_embeddings_client() -> EmbeddingsClient:
    """Get embeddings client"""
    return EmbeddingsClient(settings)


@lru_cache()
def get_chroma_client() -> ChromaDBClient:
    """Get ChromaDB HTTP client"""
    return ChromaDBClient(settings)


@lru_cache()
def get_vector_db_repository(
    chroma_client: Annotated[ChromaDBClient, Depends(get_chroma_client)],
    embeddings_client: Annotated[EmbeddingsClient, Depends(get_embeddings_client)],
) -> VectorDBRepository:
    """Get vector database repository"""
    return VectorDBRepository(settings, chroma_client, embeddings_client)


# Type aliases for dependency injection
LLMClientDep = Annotated[LLMClient, Depends(get_llm_client)]
EmbeddingsClientDep = Annotated[EmbeddingsClient, Depends(get_embeddings_client)]
ChromaClientDep = Annotated[ChromaDBClient, Depends(get_chroma_client)]
VectorDBDep = Annotated[VectorDBRepository, Depends(get_vector_db_repository)]


# ============================================================================
# Service Dependencies (Request-scoped)
# ============================================================================
def get_splitter_factory(
    embeddings_client: EmbeddingsClientDep,
) -> TextSplitterFactory:
    """Get text splitter factory."""
    return TextSplitterFactory(settings, embeddings_client.client)


def get_ingestion_service(
    vdb_repo: VectorDBDep,
    splitter_factory: Annotated[TextSplitterFactory, Depends(get_splitter_factory)],
) -> DocumentIngestionService:
    """Get document ingestion service."""
    return DocumentIngestionService(vdb_repo, splitter_factory)


# Type aliases
SplitterFactoryDep = Annotated[TextSplitterFactory, Depends(get_splitter_factory)]
IngestionServiceDep = Annotated[DocumentIngestionService, Depends(get_ingestion_service)]


# ============================================================================
# RAG Query Services
# ============================================================================
def get_qa_service(
    llm_client: LLMClientDep,
    vdb_repo: VectorDBDep,
) -> QAService:
    """Get standard QA service."""
    from app.services.rag.qa_service import QAService

    return QAService(settings, llm_client, vdb_repo)


def get_rerank_service(
    llm_client: LLMClientDep,
    vdb_repo: VectorDBDep,
) -> RerankService:
    """Get rerank QA service."""
    from app.services.rag.rerank_service import RerankService

    return RerankService(settings, llm_client, vdb_repo)


# Type aliases
QAServiceDep = Annotated[QAService, Depends(get_qa_service)]
RerankServiceDep = Annotated[RerankService, Depends(get_rerank_service)]
