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
            llm_temperature=0.05,
            llm_max_tokens=4000,
            llm_top_p=0.1,
            use_vertex_ai=False,
        )
        mock_chat_openai.return_value = MagicMock()

        # Act
        client = LLMClient(settings)

        # Assert
        mock_chat_openai.assert_called_once_with(
            model=settings.openai_model,
            api_key=ANY,  # SecretStr can't be compared
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            top_p=settings.llm_top_p,
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
            llm_temperature=0.7,
            llm_max_tokens=2000,
            llm_top_p=0.9,
            use_vertex_ai=False,
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

    @patch("app.infrastructure.llm.client.ChatVertexAI")
    def test_llm_client_vertex_ai_initialization(self, mock_chat_vertex_ai):
        # Arrange
        settings = Settings(
            local_llm=False,
            vertex_ai_model="gemini-2.5-flash",
            vertex_ai_location="us-central1",
            llm_temperature=0.05,
            llm_max_tokens=4000,
            llm_top_p=0.1,
            use_vertex_ai=True,
        )
        mock_chat_vertex_ai.return_value = MagicMock()

        # Act
        client = LLMClient(settings)

        # Assert
        mock_chat_vertex_ai.assert_called_once_with(
            model=settings.vertex_ai_model,
            project=settings.vertex_ai_project,
            location=settings.vertex_ai_location,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            top_p=settings.llm_top_p,
        )
        self.assertIsNotNone(client.client)

    @patch("app.infrastructure.llm.client.ChatVertexAI")
    def test_llm_client_vertex_ai_custom_settings(self, mock_chat_vertex_ai):
        """Test LLMClient with using Vertex AI custom settings."""
        # Arrange
        custom_settings = Settings(
            local_llm=False,
            vertex_ai_model="custom-gemini-model",
            vertex_ai_location="us-central1",
            llm_temperature=0.7,
            llm_max_tokens=2000,
            llm_top_p=0.9,
            use_vertex_ai=True,
        )
        mock_chat_vertex_ai.return_value = MagicMock()

        # Act
        client = LLMClient(custom_settings)

        # Assert
        mock_chat_vertex_ai.assert_called_once_with(
            model="custom-gemini-model",
            project=custom_settings.vertex_ai_project,
            location="us-central1",
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
            llm_temperature=0.7,
            llm_max_tokens=2000,
            llm_top_p=0.9,
        )
        mock_chat_ollama.return_value = MagicMock()

        # Act
        client = LLMClient(custom_settings)

        # Assert
        mock_chat_ollama.assert_called_once_with(
            model=custom_settings.ollama_model,
            reasoning=custom_settings.ollama_thinking,
            base_url=custom_settings.ollama_base_url,
            temperature=custom_settings.llm_temperature,
            top_p=custom_settings.llm_top_p,
        )
        self.assertIsNotNone(client.client)


if __name__ == "__main__":
    unittest.main()
