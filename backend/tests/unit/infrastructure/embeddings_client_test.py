import unittest
from unittest.mock import ANY, MagicMock, patch

from app.core.config import Settings
from app.infrastructure.embeddings.client import EmbeddingsClient


class TestEmbeddingsClient(unittest.TestCase):
    @patch("app.infrastructure.embeddings.client.OpenAIEmbeddings")
    def test_embeddings_client_openai_initialization(self, mock_openai_embeddings):
        # Arrange
        settings = Settings(
            local_llm=False,
            openai_api_key="test-key",
            embeddings_model="embeddings-model",
        )
        mock_openai_embeddings.return_value = MagicMock()

        # Act
        client = EmbeddingsClient(settings)

        # Assert
        mock_openai_embeddings.assert_called_once_with(
            model=settings.embeddings_model,
            api_key=ANY,  # SecretStr can't be compared
        )
        self.assertIsNotNone(client.client)

    @patch("app.infrastructure.embeddings.client.OllamaEmbeddings")
    def test_embeddings_client_ollama_initialization(self, mock_ollama_embeddings):
        # Arrange
        settings = Settings(
            local_llm=True, ollama_embeddings_model="embeddings-model", ollama_base_url="some_url"
        )
        mock_ollama_embeddings.return_value = MagicMock()

        # Act
        client = EmbeddingsClient(settings)

        # Assert
        mock_ollama_embeddings.assert_called_once_with(
            model=settings.ollama_embeddings_model, base_url=settings.ollama_base_url
        )
        self.assertIsNotNone(client.client)


if __name__ == "__main__":
    unittest.main()
