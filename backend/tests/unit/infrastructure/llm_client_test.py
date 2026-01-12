import unittest
from unittest.mock import ANY, MagicMock, patch

from app.core.config import Settings
from app.infrastructure.llm.client import LLMClient


class TestLLMClient(unittest.TestCase):
    @patch("app.infrastructure.llm.client.ChatOpenAI")
    def test_llm_client_openai_initialization(self, mock_chat_openai):
        # Arrange
        settings = Settings(
            local_llm=False,
            openai_api_key="test-key",
            openai_model="gpt-4o-mini",
            openai_temperature=0.05,
            openai_max_tokens=4000,
            openai_top_p=0.1,
        )
        mock_chat_openai.return_value = MagicMock()

        # Act
        client = LLMClient(settings)

        # Assert
        mock_chat_openai.assert_called_once_with(
            model=settings.openai_model,
            api_key=ANY,  # SecretStr can't be compared
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens,
            top_p=settings.openai_top_p,
        )
        self.assertIsNotNone(client.client)

    @patch("app.infrastructure.llm.client.ChatOpenAI")
    def test_llm_client_openai_custom_settings(self, mock_chat_openai):
        """Test LLMClient with using OpenAI custom settings."""
        # Arrange
        custom_settings = Settings(
            local_llm=False,
            openai_api_key="custom-key",
            openai_model="gpt-4",
            openai_temperature=0.7,
            openai_max_tokens=2000,
            openai_top_p=0.9,
        )
        mock_chat_openai.return_value = MagicMock()

        # Act
        client = LLMClient(custom_settings)

        # Assert
        mock_chat_openai.assert_called_once_with(
            model="gpt-4",
            api_key=ANY,
            temperature=0.7,
            max_tokens=2000,
            top_p=0.9,
        )
        self.assertIsNotNone(client.client)

    @patch("app.infrastructure.llm.client.ChatOllama")
    def test_llm_client_ollama_custom_settings(self, mock_chat_ollama):
        """Test LLMClient using Ollama with custom settings."""
        # Arrange
        custom_settings = Settings(
            local_llm=True,
            ollama_model="some_model",
            ollama_base_url="some_url",
            ollama_thinking=False,
            openai_temperature=0.7,
            openai_max_tokens=2000,
            openai_top_p=0.9,
        )
        mock_chat_ollama.return_value = MagicMock()

        # Act
        client = LLMClient(custom_settings)

        # Assert
        mock_chat_ollama.assert_called_once_with(
            model=custom_settings.ollama_model,
            reasoning=custom_settings.ollama_thinking,
            base_url=custom_settings.ollama_base_url,
            temperature=custom_settings.openai_temperature,
            top_p=custom_settings.openai_top_p,
        )
        self.assertIsNotNone(client.client)


if __name__ == "__main__":
    unittest.main()
