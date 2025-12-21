import os
from functools import lru_cache
from pathlib import Path

import requests
from google.api_core.exceptions import GoogleAPIError
from google.cloud import secretmanager
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.utils.logger import logger


def _get_gcp_project_id() -> str:
    """Get GCP project ID from metadata server (works in Cloud Run) or env var."""
    try:
        # (Cloud Run, Compute Engine)
        response = requests.get(
            "http://metadata.google.internal/computeMetadata/v1/project/project-id",
            headers={"Metadata-Flavor": "Google"},
            timeout=1,
        )
        return response.text

    except requests.RequestException:
        logger.info("Not running in GCP environment, trying env var...")
        return os.getenv("PROJECT_ID", "")

    except Exception as e:
        logger.info(f"Exception: {e}")
        logger.info("Running locally, retrieving project_id using env var...")
        return os.getenv("PROJECT_ID", "")


@lru_cache(maxsize=10)
def _get_secret(secret_id: str) -> str:
    """Fetch secret from GCP Secret Manager. Cached."""
    try:
        project_id = _get_gcp_project_id()
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")

    except GoogleAPIError:
        logger.info(f"Secret {secret_id} not found in GCP Secret Manager.")
        return ""

    except Exception as e:
        logger.info(f"Exception: {e}")
        logger.info("Running locally, retrieving from env var...")
        return os.getenv(secret_id.upper().replace("-", "_"), "")


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # LLM configuration
    local_llm: bool = Field(default=False, env="LOCAL_LLM")  # type: ignore[call-overload]

    # Ollama Configuration
    # ollama_model: str = Field(default="llama3.2")
    ollama_model: str = Field(default="qwen3:8b")
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_thinking: bool = Field(default=False)
    ollama_embeddings_model: str = Field(default="nomic-embed-text:v1.5")  # type: ignore[call-arg]

    # OpenAI Configuration
    # openai_api_key: str = Field(default="", env="OPENAI_API_KEY")  # type: ignore[call-overload]
    @property
    def openai_api_key(self) -> str:
        return _get_secret("openai-api-key")

    openai_model: str = Field(default="gpt-4.1-nano")
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

    # cohere_api_key: str = Field(default="", env="COHERE_API_KEY")  # type: ignore[call-overload]
    @property
    def cohere_api_key(self) -> str:
        return _get_secret("cohere-api-key")

    # Application
    app_host: str = Field(default="0.0.0.0", env="HOST")  # type: ignore[call-overload]
    app_port: int = Field(default=8106)

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / "backend.env"),
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
