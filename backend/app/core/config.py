from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.helpers import VectorDBType, _get_gcp_project_id, get_secret


class Settings(BaseSettings):
    """Application settings from environment variables."""

    #! Important: Keep synced with k8s/base/backend/configmap.yaml and configmap-local.yaml
    # LLM configuration
    local_llm: bool = Field(default=False, validation_alias="LOCAL_LLM")

    # Cloud llm configuration
    use_vertex_ai: bool = Field(default=False, validation_alias="USE_VERTEX_AI")

    # Ollama Configuration
    # ollama_model: str = Field(default="llama3.2")
    ollama_model: str = Field(default="qwen3:8b")
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_thinking: bool = Field(default=False)
    ollama_embeddings_model: str = Field(
        default="nomic-embed-text-v2-moe", validation_alias="OLLAMA_EMBEDDINGS_MODEL"
    )

    # Vertex AI Configuration
    vertex_ai_model: str = Field(default="gemini-2.5-flash")
    vertex_ai_location: str = Field(default="us-central1")

    @property
    def vertex_ai_project(self) -> str:
        return _get_gcp_project_id()

    # OpenAI Configuration
    @property
    def openai_api_key(self) -> str:
        return get_secret("openai-api-key")

    openai_model: str = Field(default="gpt-4.1-nano")
    llm_temperature: float = Field(default=0.05)
    llm_max_tokens: int = Field(default=4000)
    llm_top_p: float = Field(default=0.1)

    # Embeddings Configuration
    # Embeddings model are model agnostic, but:
    # - ada-002 performs better with openai models
    # - text-multilingual-embedding-002 performs better with vertex ai models
    embeddings_model: str = Field(default="text-embedding-ada-002")
    # embeddings_model: str = Field(default="text-multilingual-embedding-002")

    # Vector Database Selection
    # * Default to ChromaDB
    vector_db_type: VectorDBType = Field(
        default=VectorDBType.CHROMA, validation_alias="VECTOR_DB_TYPE"
    )

    # ChromaDB Configuration
    chromadb_host: str = Field(default="localhost", validation_alias="CHROMADB_HOST")
    chromadb_port: int = Field(default=8000, validation_alias="CHROMADB_PORT")
    chromadb_tenant: str = Field(default="dev")
    chromadb_database: str = Field(default="rag-database")
    chromadb_collection: str = Field(default="rag-docs")

    # Postgres Configuration
    # * Based on: https://docs.langchain.com/oss/python/integrations/vectorstores/pgvectorstore
    pgvector_host: str = Field(default="localhost", validation_alias="PGVECTOR_HOST")
    pgvector_port: int = Field(default=6024, validation_alias="PGVECTOR_PORT")
    pgvector_user: str = Field(default="langchain", validation_alias="PGVECTOR_USER")
    pgvector_password: str = Field(default="langchain", validation_alias="PGVECTOR_PASSWORD")
    pgvector_database: str = Field(default="langchain", validation_alias="PGVECTOR_DATABASE")
    pgvector_schema: str = Field(default="vector", validation_alias="PGVECTOR_SCHEMA")
    pgvector_table: str = Field(default="rag_documents", validation_alias="PGVECTOR_TABLE")
    db_schema: str = Field(default="app", validation_alias="DB_SCHEMA")

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
    app_host: str = Field(default="0.0.0.0", validation_alias="HOST")
    app_port: int = Field(default=8106)

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    def get_vector_size(self) -> int:
        model_sizes = {
            # Ollama models
            "nomic-embed-text:v1.5": 768,
            "nomic-embed-text-v2-moe": 256,
            # OpenAI models
            "text-embedding-ada-002": 1536,
            "text-embedding-3-large": 3072,
            #  Vertex AI models
            "text-multilingual-embedding-002": 768,
            "gemini-embedding-001": 3072,
        }

        # Determine which model is being used
        if self.local_llm:
            current_model = self.ollama_embeddings_model
        else:
            current_model = self.embeddings_model

        return model_sizes.get(current_model, 768)


settings = Settings()
