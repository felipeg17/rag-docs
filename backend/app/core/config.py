from pathlib import Path
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.helpers import VectorDBType, get_secret


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # LLM configuration
    local_llm: Annotated[bool, Field(env="LOCAL_LLM")] = False

    # Ollama Configuration
    # ollama_model: str = Field(default="llama3.2")
    ollama_model: str = Field(default="qwen3:8b")
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_thinking: bool = Field(default=False)
    ollama_embeddings_model: Annotated[str, Field(env="OLLAMA_EMBEDDINGS_MODEL")] = (
        "nomic-embed-text:v1.5"
    )

    # OpenAI Configuration
    @property
    def openai_api_key(self) -> str:
        return get_secret("openai-api-key")

    openai_model: str = Field(default="gpt-4.1-nano")
    openai_temperature: float = Field(default=0.05)
    openai_max_tokens: int = Field(default=4000)
    openai_top_p: float = Field(default=0.1)

    # Embeddings Configuration
    embeddings_model: str = Field(default="text-embedding-ada-002")

    # Vector Database Selection
    vector_db_type: Annotated[VectorDBType, Field(env="VECTOR_DB_TYPE")] = VectorDBType.PGVECTOR

    # ChromaDB Configuration
    chromadb_host: Annotated[str, Field(env="CHROMADB_HOST")] = "localhost"
    chromadb_port: Annotated[int, Field(env="CHROMADB_PORT")] = 9000
    chromadb_tenant: str = Field(default="dev")
    chromadb_database: str = Field(default="rag-database")
    chromadb_collection: str = Field(default="rag-docs")

    # PGVector Configuration
    # * Based on: https://docs.langchain.com/oss/python/integrations/vectorstores/pgvectorstore
    pgvector_host: Annotated[str, Field(env="PGVECTOR_HOST")] = "localhost"
    pgvector_port: Annotated[int, Field(env="PGVECTOR_PORT")] = 6024
    pgvector_user: Annotated[str, Field(env="PGVECTOR_USER")] = "langchain"
    pgvector_password: Annotated[str, Field(env="PGVECTOR_PASSWORD")] = "langchain"
    pgvector_database: Annotated[str, Field(env="PGVECTOR_DATABASE")] = "langchain"
    pgvector_schema: Annotated[str, Field(env="PGVECTOR_SCHEMA")] = "public"
    pgvector_table: Annotated[str, Field(env="PGVECTOR_TABLE")] = "rag_documents"

    # RAG Configuration
    default_chunk_size: int = Field(default=800)
    default_chunk_overlap: int = Field(default=50)
    default_k_results: int = Field(default=4)
    default_rerank_top_n: int = Field(default=3)

    # Cohere Configuration (for reranking)
    cohere_model: str = Field(default="rerank-v3.5")

    @property
    def cohere_api_key(self) -> str:
        return get_secret("cohere-api-key")

    # Application
    app_host: Annotated[str, Field(env="HOST")] = "0.0.0.0"
    app_port: int = Field(default=8106)

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / "backend.env"),
        case_sensitive=False,
        extra="ignore",
    )

    def get_vector_size(self) -> int:
        model_sizes = {
            # Ollama models
            "nomic-embed-text:v1.5": 768,
            # OpenAI models
            "text-embedding-ada-002": 1536,
            "text-embedding-3-large": 3072,
        }

        # Determine which model is being used
        if self.local_llm:
            current_model = self.ollama_embeddings_model
        else:
            current_model = self.embeddings_model

        return model_sizes.get(current_model, 768)


settings = Settings()
