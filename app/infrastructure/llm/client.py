from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.config import Settings


class LLMClient:
    """OpenAI LLM client wrapper."""

    def __init__(self, settings: Settings) -> None:
        self._client = ChatOpenAI(
            model=settings.openai_model,
            api_key=SecretStr(settings.openai_api_key),
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens,
            top_p=settings.openai_top_p,
        )

    @property
    def client(self) -> ChatOpenAI:
        return self._client
