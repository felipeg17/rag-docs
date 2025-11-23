from langchain_openai import OpenAIEmbeddings

from app.core.config import Settings


class EmbeddingsClient:
    """OpenAI embeddings client wrapper."""

    def __init__(self, settings: Settings) -> None:
        self._client = OpenAIEmbeddings(
            model=settings.embeddings_model, api_key=settings.openai_api_key
        )

    @property
    def client(self) -> OpenAIEmbeddings:
        return self._client
