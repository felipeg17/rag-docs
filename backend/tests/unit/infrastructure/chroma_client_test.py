import unittest
import uuid
from unittest.mock import MagicMock, patch

import chromadb
from chromadb.config import Settings as ChromaSettings

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
        mock_collection.configuration_json = {"hnsw": {"space": "cosine"}}
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
        mock_client_instance.create_collection.assert_called_once_with(
            name="new-collection", metadata={"hnsw:space": "cosine"}
        )


class TestChromaDBClientCosineMetric(unittest.TestCase):
    """AC-15 (c) and AC-16 over an in-memory Chroma; no network."""

    def setUp(self):
        self.settings = Settings(chromadb_host="localhost", chromadb_port=9000)
        self.ephemeral = chromadb.EphemeralClient(
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.name = f"coll-{uuid.uuid4().hex}"

    def _client(self) -> ChromaDBClient:
        with patch(
            "app.infrastructure.vector_db.chroma_client.chromadb.HttpClient",
            return_value=self.ephemeral,
        ):
            return ChromaDBClient(self.settings)

    def test_creates_cosine_collection(self):
        self._client().get_or_create_collection(self.name)

        collection = self.ephemeral.get_collection(self.name)
        self.assertEqual(collection.metadata, {"hnsw:space": "cosine"})
        self.assertEqual(collection.configuration_json["hnsw"]["space"], "cosine")

    def test_existing_cosine_collection_is_accepted(self):
        self.ephemeral.create_collection(self.name, metadata={"hnsw:space": "cosine"})

        self._client().get_or_create_collection(self.name)

    def test_existing_l2_collection_is_refused_and_untouched(self):
        collection = self.ephemeral.create_collection(self.name, metadata={"hnsw:space": "l2"})
        collection.add(ids=["1"], embeddings=[[0.1, 0.2]], documents=["d"])

        with self.assertRaises(RuntimeError) as ctx:
            self._client().get_or_create_collection(self.name)

        for text in (self.name, "l2", "recreate"):
            self.assertIn(text, str(ctx.exception))
        after = self.ephemeral.get_collection(self.name)
        self.assertEqual(after.configuration_json["hnsw"]["space"], "l2")
        self.assertEqual(after.count(), 1)

    def test_existing_collection_without_metadata_is_refused(self):
        self.ephemeral.create_collection(self.name)

        with self.assertRaises(RuntimeError) as ctx:
            self._client().get_or_create_collection(self.name)

        self.assertIn("l2", str(ctx.exception))
        self.assertIn(self.name, str(ctx.exception))

    def _mocked_client(self, configuration_json, metadata=None) -> ChromaDBClient:
        http = MagicMock()
        http.get_collection.return_value = MagicMock(
            metadata=metadata, configuration_json=configuration_json
        )
        with patch(
            "app.infrastructure.vector_db.chroma_client.chromadb.HttpClient",
            return_value=http,
        ):
            return ChromaDBClient(self.settings)

    def test_server_1_0_0_shape_l2_is_refused(self):
        client = self._mocked_client({"hnsw_configuration": {"space": "l2"}})

        with self.assertRaises(RuntimeError):
            client.get_or_create_collection(self.name)

    def test_configuration_only_cosine_is_accepted(self):
        """AC-16 (v): no metadata, truthful configuration (server 1.0.0 never returns this)."""
        client = self._mocked_client({"hnsw_configuration": {"space": "cosine"}})

        client.get_or_create_collection(self.name)

    def test_server_1_0_0_metadata_cosine_with_l2_configuration_is_accepted(self):
        """AC-16 (vi): server 1.0.0 reports l2 for a cosine collection this code created."""
        client = self._mocked_client(
            {"_type": "CollectionConfigurationInternal", "hnsw_configuration": {"space": "l2"}},
            metadata={"hnsw:space": "cosine"},
        )

        client.get_or_create_collection(self.name)


if __name__ == "__main__":
    unittest.main()
