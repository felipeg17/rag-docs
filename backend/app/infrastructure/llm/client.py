from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.config import Settings


class LLMClient:
    """LLM client wrapper."""

    def __init__(self, settings: Settings) -> None:
        self._client: ChatOpenAI | ChatOllama
        self._llm_model: str

        if settings.local_llm:
            self._client = ChatOllama(
                model=settings.ollama_model,
                reasoning=settings.ollama_thinking,
                base_url=settings.ollama_base_url,
                temperature=settings.openai_temperature,
                top_p=settings.openai_top_p,
            )
            self._llm_model = settings.ollama_model

        else:
            self._client = ChatOpenAI(
                model=settings.openai_model,  # type: ignore[call-arg]
                api_key=SecretStr(settings.openai_api_key),
                temperature=settings.openai_temperature,
                max_tokens=settings.openai_max_tokens,
                top_p=settings.openai_top_p,
            )
            self._llm_model = self._client.model_name

    @property
    def client(self) -> ChatOpenAI | ChatOllama:
        return self._client

    @property
    def llm_model(self) -> str:
        return self._llm_model
