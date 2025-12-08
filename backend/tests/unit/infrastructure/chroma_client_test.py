import unittest
from unittest.mock import MagicMock, patch

from app.core.config import Settings
from app.infrastructure.vector_db.chroma_client import ChromaDBClient


class TestChromaDBClient(unittest.TestCase):
    def setUp(self):
        """Set up test settings."""
        self.settings = Settings(
            chromadb_host="localhost",
            chromadb_port=9000,
            chromadb_tenant="test-tenant",
            chromadb_database="test-db",
        )

    @patch("app.infrastructure.vector_db.chroma_client.chromadb.HttpClient")
    def test_chroma_client_initialization(self, mock_http_client):
        """Test that ChromaDBClient initializes HttpClient with correct settings."""
        # Arrange
        mock_http_client.return_value = MagicMock()

        # Act
        client = ChromaDBClient(self.settings)

        # Assert
        mock_http_client.assert_called_once_with(
            host=f"http://{self.settings.chromadb_host}:{self.settings.chromadb_port}",
            tenant=self.settings.chromadb_tenant,
            database=self.settings.chromadb_database,
        )
        self.assertIsNotNone(client.client)

    @patch("app.infrastructure.vector_db.chroma_client.chromadb.HttpClient")
    def test_heartbeat(self, mock_http_client):
        """Test heartbeat method calls client heartbeat."""
        # Arrange
        mock_client_instance = MagicMock()
        mock_client_instance.heartbeat.return_value = 1234567890
        mock_http_client.return_value = mock_client_instance

        client = ChromaDBClient(self.settings)

        # Act
        result = client.heartbeat()

        # Assert
        self.assertEqual(result, 1234567890)
        mock_client_instance.heartbeat.assert_called_once()

    @patch("app.infrastructure.vector_db.chroma_client.chromadb.HttpClient")
    def test_get_or_create_collection_existing(self, mock_http_client):
        """Test get_or_create_collection when collection exists."""
        # Arrange
        mock_client_instance = MagicMock()
        mock_collection = MagicMock()
        mock_collection.name = "test-collection"
        mock_client_instance.get_collection.return_value = mock_collection
        mock_http_client.return_value = mock_client_instance

        client = ChromaDBClient(self.settings)

        # Act
        client.get_or_create_collection("test-collection")

        # Assert
        mock_client_instance.get_collection.assert_called_once_with(name="test-collection")

    @patch("app.infrastructure.vector_db.chroma_client.chromadb.HttpClient")
    def test_get_or_create_collection_create_new(self, mock_http_client):
        """Test get_or_create_collection when collection doesn't exist."""
        # Arrange
        mock_client_instance = MagicMock()
        mock_client_instance.get_collection.side_effect = Exception("Collection not found")
        mock_collection = MagicMock()
        mock_collection.name = "new-collection"
        mock_client_instance.create_collection.return_value = mock_collection
        mock_http_client.return_value = mock_client_instance

        client = ChromaDBClient(self.settings)

        # Act
        client.get_or_create_collection("new-collection")

        # Assert
        mock_client_instance.get_collection.assert_called_once_with(name="new-collection")
        mock_client_instance.create_collection.assert_called_once_with(name="new-collection")


if __name__ == "__main__":
    unittest.main()
