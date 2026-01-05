from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, VectorDBType, settings
from app.infrastructure.database.client import DatabaseClient
from app.infrastructure.database.repositories.document_repository import DocumentRepository
from app.infrastructure.database.repositories.interaction_repository import (
    QAInteractionRepository,
    SearchInteractionRepository,
)
from app.infrastructure.embeddings.client import EmbeddingsClient
from app.infrastructure.llm.client import LLMClient
from app.infrastructure.vector_db.chroma_client import ChromaDBClient
from app.infrastructure.vector_db.pgvector_client import PGVectorClient
from app.infrastructure.vector_db.pgvector_repository import PGVectorDBRepository
from app.infrastructure.vector_db.repository import VectorDBRepository
from app.services.document.text_splitter import TextSplitterFactory
from app.services.ingest.ingestion import DocumentIngestionService
from app.services.persistence.document_service import DocumentService
from app.services.persistence.interaction_service import InteractionService
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
def get_pgvector_client() -> PGVectorClient:
    """Get PGVector PostgreSQL client"""
    return PGVectorClient(settings)


@lru_cache()
def get_vector_db_repository(
    embeddings_client: Annotated[EmbeddingsClient, Depends(get_embeddings_client)],
) -> VectorDBRepository | PGVectorDBRepository:
    """Get vector database repository (Chroma or PGVector based on settings)"""
    if settings.vector_db_type == VectorDBType.PGVECTOR:
        pgvector_client = get_pgvector_client()
        return PGVectorDBRepository(settings, pgvector_client, embeddings_client)
    else:
        chroma_client = get_chroma_client()
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
    return TextSplitterFactory(settings, embeddings_client)


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
    return QAService(settings, llm_client, vdb_repo)


def get_rerank_service(
    llm_client: LLMClientDep,
    vdb_repo: VectorDBDep,
) -> RerankService:
    """Get rerank QA service."""
    return RerankService(settings, llm_client, vdb_repo)


# Type aliases
QAServiceDep = Annotated[QAService, Depends(get_qa_service)]
RerankServiceDep = Annotated[RerankService, Depends(get_rerank_service)]


# ============================================================================
# Database Dependencies (Persistent Layer)
# ============================================================================
@lru_cache()
def get_db_client() -> DatabaseClient:
    """Get database client"""
    return DatabaseClient(settings)


def get_db_session(db_client: Annotated[DatabaseClient, Depends(get_db_client)]):
    """Get database session with automatic cleanup."""
    session = db_client.get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Repository Dependencies
def get_document_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> DocumentRepository:
    """Get document repository."""
    return DocumentRepository(session)


def get_search_interaction_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> SearchInteractionRepository:
    """Get search interaction repository."""
    return SearchInteractionRepository(session)


def get_qa_interaction_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> QAInteractionRepository:
    """Get Q&A interaction repository."""
    return QAInteractionRepository(session)


# Service Dependencies
def get_document_service(
    doc_repo: Annotated[DocumentRepository, Depends(get_document_repository)],
) -> DocumentService:
    """Get document service."""
    return DocumentService(doc_repo)


def get_interaction_service(
    search_repo: Annotated[SearchInteractionRepository, Depends(get_search_interaction_repository)],
    qa_repo: Annotated[QAInteractionRepository, Depends(get_qa_interaction_repository)],
) -> InteractionService:
    """Get interaction service."""
    return InteractionService(search_repo, qa_repo)


# Type aliases for convenience
DBSessionDep = Annotated[Session, Depends(get_db_session)]
DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
InteractionServiceDep = Annotated[InteractionService, Depends(get_interaction_service)]

# region
# ============================================================================
# Flow
# HTTP POST /api/v1/documents
#     ↓
# FastAPI sees: doc_service: DocumentServiceDep
#     ↓
# Resolves dependency chain:
#     ↓
# 1. get_db_client()              [Cached - reuses existing]
#     ↓
# 2. get_db_session(db_client)    [Creates new session]
#     ↓
# 3. get_document_repository(session)
#     ↓
# 4. get_document_service(doc_repo)
#     ↓
# 5. Calls your endpoint: create_doc(doc_service)
#     ↓
# Your code runs: doc_service.create_document(...)
#     ↓
# Endpoint returns successfully
#     ↓
# FastAPI cleanup (reverse order):
#     ↓
# session.commit()   [From get_db_session]
#     ↓
# session.close()    [From get_db_session]
#     ↓
# HTTP 201 Created

# If endpoint raises exception:
# Your code raises: HTTPException(400, "Invalid PDF")
#     ↓
# FastAPI cleanup:
#     ↓
# session.rollback()  [From get_db_session]
#     ↓
# session.close()     [From get_db_session]
#     ↓
# HTTP 400 Bad Request
# ============================================================================
# endregion
