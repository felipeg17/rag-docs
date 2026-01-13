from typing import Union

from langchain_google_vertexai import ChatVertexAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.config import Settings


LLMClientType = Union[ChatOpenAI, ChatOllama, ChatVertexAI]


class LLMClient:
    """LLM client wrapper."""

    def __init__(self, settings: Settings) -> None:
        self._client: LLMClientType
        self._llm_model: str

        if settings.local_llm:
            self._client = ChatOllama(
                model=settings.ollama_model,
                reasoning=settings.ollama_thinking,
                base_url=settings.ollama_base_url,
                temperature=settings.llm_temperature,
                top_p=settings.llm_top_p,
            )
            self._llm_model = settings.ollama_model

        else:
            if settings.use_vertex_ai:
                self._client = ChatVertexAI(
                    model=settings.vertex_ai_model,
                    project=settings.vertex_ai_project,
                    location=settings.vertex_ai_location,
                    temperature=settings.llm_temperature,
                    max_tokens=settings.llm_max_tokens,
                    top_p=settings.llm_top_p,
                )
                self._llm_model = settings.vertex_ai_model
                return

            self._client = ChatOpenAI(
                model=settings.openai_model,  # type: ignore[call-arg]
                api_key=SecretStr(settings.openai_api_key),
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                top_p=settings.llm_top_p,
            )
            self._llm_model = self._client.model_name

    @property
    def client(self) -> LLMClientType:
        return self._client

    @property
    def llm_model(self) -> str:
        return self._llm_model
