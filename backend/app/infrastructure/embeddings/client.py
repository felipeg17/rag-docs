from typing import Union

from langchain_google_vertexai import VertexAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr

from app.core.config import Settings


EmbeddingsClientType = Union[OllamaEmbeddings, OpenAIEmbeddings, VertexAIEmbeddings]


class EmbeddingsClient:
    """Embeddings client wrapper."""

    def __init__(self, settings: Settings) -> None:
        self._client: EmbeddingsClientType
        self._embeddings_model: str

        if settings.local_llm:
            self._client = OllamaEmbeddings(
                model=settings.ollama_embeddings_model,
                base_url=settings.ollama_base_url,
            )
            self._embeddings_model = settings.ollama_embeddings_model

        else:
            if settings.use_vertex_ai:
                self._client = VertexAIEmbeddings(
                    model_name=settings.embeddings_model,
                    project=settings.vertex_ai_project,
                    location=settings.vertex_ai_location,
                )
                self._embeddings_model = settings.embeddings_model
                return

            self._client = OpenAIEmbeddings(
                model=settings.embeddings_model,
                api_key=SecretStr(settings.openai_api_key),  # type: ignore[call-arg]
            )
            self._embeddings_model = settings.embeddings_model

    @property
    def client(self) -> EmbeddingsClientType:
        return self._client

    @property
    def embeddings_model(self) -> str:
        return self._embeddings_model
