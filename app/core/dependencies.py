# app/core/dependencies.py
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, settings


# ============================================================================
# Configuration Dependency
# ============================================================================
def get_settings() -> Settings:
    return settings


SettingsDep = Annotated[Settings, Depends(get_settings)]


# ============================================================================
# Infrastructure Dependencies (Singletons)
# ============================================================================
# NOTE: These will be implemented in Phase 2
# For now, just define the signatures

# @lru_cache()
# def get_llm_client(settings: SettingsDep) -> LLMClient:
#     """Get LLM client (singleton)."""
#     return LLMClient(settings)

# @lru_cache()
# def get_embeddings_client(settings: SettingsDep) -> EmbeddingsClient:
#     """Get embeddings client (singleton)."""
#     return EmbeddingsClient(settings)

# @lru_cache()
# def get_chroma_client(settings: SettingsDep) -> ChromaClient:
#     """Get ChromaDB client (singleton)."""
#     return ChromaClient(settings)


# ============================================================================
# Service Dependencies (Request-scoped)
# ============================================================================
# NOTE: These will be implemented in Phase 3
# For now, just define the signatures

# def get_vector_db_repository(
#     chroma_client: ChromaClient = Depends(get_chroma_client),
#     embeddings_client: EmbeddingsClient = Depends(get_embeddings_client),
# ) -> VectorDBRepository:
#     """Get VectorDB repository."""
#     return VectorDBRepository(chroma_client, embeddings_client)

# def get_ingestion_service(
#     vdb_repo: VectorDBRepository = Depends(get_vector_db_repository),
# ) -> IngestionService:
#     """Get document ingestion service."""
#     return IngestionService(vdb_repo)
