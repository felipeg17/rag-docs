import unittest
from unittest.mock import ANY, MagicMock, patch

from app.core.config import Settings
from app.infrastructure.embeddings.client import EmbeddingsClient


class TestEmbeddingsClient(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(
            openai_api_key="test-key",
            embeddings_model="embeddings-model",
        )

    @patch("app.infrastructure.embeddings.client.OpenAIEmbeddings")
    def test_embeddings_client_initialization(self, mock_openai_embeddings):
        # Arrange
        mock_openai_embeddings.return_value = MagicMock()

        # Act
        client = EmbeddingsClient(self.settings)

        # Assert
        mock_openai_embeddings.assert_called_once_with(
            model=self.settings.embeddings_model,
            api_key=ANY,  # SecretStr can't be compared
        )
        self.assertIsNotNone(client.client)


if __name__ == "__main__":
    unittest.main()
