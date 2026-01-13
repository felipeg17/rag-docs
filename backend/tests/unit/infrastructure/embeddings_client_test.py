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
            use_vertex_ai=False,
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

    @patch("app.infrastructure.embeddings.client.VertexAIEmbeddings")
    def test_embeddings_client_vertex_ai_initialization(self, mock_vertex_ai_embeddings):
        # Arrange
        settings = Settings(
            local_llm=False,
            embeddings_model="embeddings-model",
            use_vertex_ai=True,
            vertex_ai_project="test-project",
        )
        mock_vertex_ai_embeddings.return_value = MagicMock()

        # Act
        client = EmbeddingsClient(settings)

        # Assert
        mock_vertex_ai_embeddings.assert_called_once_with(
            model_name=settings.embeddings_model,
            project=settings.vertex_ai_project,
            location=settings.vertex_ai_location,
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
