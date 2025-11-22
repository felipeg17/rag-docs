from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # OpenAI Configuration
    openai_api_key: str = Field(env="OPENAI_API_KEY")  # type: ignore[call-overload]
    openai_model: str = Field(default="gpt-4o-mini")
    openai_temperature: float = Field(default=0.05)
    openai_max_tokens: int = Field(default=4000)
    openai_top_p: float = Field(default=0.1)

    # Embeddings Configuration
    embeddings_model: str = Field(default="text-embedding-ada-002")

    # ChromaDB Configuration
    chromadb_host: str = Field(default="localhost", env="CHROMADB_HOST")  # type: ignore[call-overload]
    chromadb_port: int = Field(default=9000, env="CHROMADB_PORT")  # type: ignore[call-overload]
    chromadb_tenant: str = Field(default="dev")
    chromadb_database: str = Field(default="rag-database")
    chromadb_collection: str = Field(default="rag-docs")

    # RAG Configuration
    default_chunk_size: int = Field(default=800)
    default_chunk_overlap: int = Field(default=50)
    default_k_results: int = Field(default=4)
    default_rerank_top_n: int = Field(default=3)

    # Cohere Configuration (for reranking)
    cohere_model: str = Field(default="rerank-v3.5")
    cohere_api_key: str = Field(env="COHERE_API_KEY")  # type: ignore[call-overload]

    # Observability
    langchain_project: str = Field(default="rag-docs", env="LANGCHAIN_PROJECT")  # type: ignore[call-overload]
    langsmith_tracing: bool = Field(default=True)

    # Application
    app_host: str = Field(default="0.0.0.0", env="HOST")  # type: ignore[call-overload]
    app_port: int = Field(default=8106)

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
