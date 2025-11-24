import unittest
from unittest.mock import ANY, MagicMock, patch

from app.core.config import Settings
from app.infrastructure.llm.client import LLMClient


class TestLLMClient(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(
            openai_api_key="test-key",
            openai_model="gpt-4o-mini",
            openai_temperature=0.05,
            openai_max_tokens=4000,
            openai_top_p=0.1,
        )

    @patch("app.infrastructure.llm.client.ChatOpenAI")
    def test_llm_client_initialization(self, mock_chat_openai):
        # Arrange
        mock_chat_openai.return_value = MagicMock()

        # Act
        client = LLMClient(self.settings)

        # Assert
        mock_chat_openai.assert_called_once_with(
            model=self.settings.openai_model,
            api_key=ANY,  # SecretStr can't be compared
            temperature=self.settings.openai_temperature,
            max_tokens=self.settings.openai_max_tokens,
            top_p=self.settings.openai_top_p,
        )
        self.assertIsNotNone(client.client)

    @patch("app.infrastructure.llm.client.ChatOpenAI")
    def test_llm_client_custom_settings(self, mock_chat_openai):
        """Test LLMClient with custom settings."""
        # Arrange
        custom_settings = Settings(
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


if __name__ == "__main__":
    unittest.main()
