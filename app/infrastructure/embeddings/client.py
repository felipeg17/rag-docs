from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings

from app.core.config import Settings


class EmbeddingsClient:
    """Embeddings client wrapper."""

    def __init__(self, settings: Settings) -> None:
        self._client: OllamaEmbeddings | OpenAIEmbeddings
        self._embeddings_model: str

        if settings.local_llm:
            self._client = OllamaEmbeddings(
                model=settings.ollama_embeddings_model,
                base_url=settings.ollama_base_url,
            )
            self._embeddings_model = settings.ollama_embeddings_model

        else:
            self._client = OpenAIEmbeddings(
                model=settings.embeddings_model,
                api_key=settings.openai_api_key,  # type: ignore[call-arg]
            )
            self._embeddings_model = settings.embeddings_model

    @property
    def client(self) -> OllamaEmbeddings | OpenAIEmbeddings:
        return self._client

    @property
    def embeddings_model(self) -> str:
        return self._embeddings_model
