import unittest
from unittest.mock import MagicMock, patch

from langchain.schema import Document

from app.core.config import Settings
from app.infrastructure.vector_db.repository import VectorDBRepository


class TestVectorDBRepository(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(
            chromadb_collection="test-collection",
            chromadb_tenant="test-tenant",
            chromadb_database="test-db",
            default_k_results=4,
        )

        # Mock ChromaDBClient
        self.mock_chroma_client = MagicMock()
        self.mock_chroma_http_client = MagicMock()
        self.mock_chroma_client.client = self.mock_chroma_http_client
        self.mock_chroma_client.get_or_create_collection.return_value = None

        # Mock EmbeddingsClient
        self.mock_embeddings_client = MagicMock()
        self.mock_embeddings = MagicMock()
        self.mock_embeddings_client.client = self.mock_embeddings

    @patch("app.infrastructure.vector_db.repository.Chroma")
    def test_initialization(self, mock_chroma):
        # Arrange
        mock_chroma_instance = MagicMock()
        mock_chroma.return_value = mock_chroma_instance

        repo = VectorDBRepository(
            self.settings,
            self.mock_chroma_client,
            self.mock_embeddings_client,
        )

        # Assert
        self.mock_chroma_client.get_or_create_collection.assert_called_once_with("test-collection")
        mock_chroma.assert_called_once_with(
            collection_name="test-collection",
            embedding_function=self.mock_embeddings,
            client=self.mock_chroma_http_client,
        )
        self.assertIsNotNone(repo.vdb)

    @patch("app.infrastructure.vector_db.repository.Chroma")
    def test_add_documents(self, mock_chroma):
        # Arrange
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.add_documents.return_value = ["id1", "id2"]
        mock_chroma.return_value = mock_chroma_instance

        repo = VectorDBRepository(
            self.settings,
            self.mock_chroma_client,
            self.mock_embeddings_client,
        )

        documents = [
            Document(
                page_content="Test content",
                metadata={"titulo": "test_doc", "pagina": 0},
            )
        ]

        # Act
        result = repo.add_documents(documents)

        # Assert
        mock_chroma_instance.add_documents.assert_called_once_with(documents)
        self.assertEqual(result, ["id1", "id2"])

    @patch("app.infrastructure.vector_db.repository.Chroma")
    def test_similarity_search_with_score(self, mock_chroma):
        # Arrange
        mock_chroma_instance = MagicMock()
        expected_results = [
            (Document(page_content="Result 1", metadata={"titulo": "test"}), 0.95),
            (Document(page_content="Result 2", metadata={"titulo": "test"}), 0.87),
        ]
        mock_chroma_instance.similarity_search_with_score.return_value = expected_results
        mock_chroma.return_value = mock_chroma_instance

        repo = VectorDBRepository(
            self.settings,
            self.mock_chroma_client,
            self.mock_embeddings_client,
        )

        # Act
        results = repo.similarity_search_with_score(query="test query", k=2)

        # Assert
        mock_chroma_instance.similarity_search_with_score.assert_called_once_with(
            query="test query",
            k=2,
            filter={"tipo-documento": "documento-pdf"},
            where_document={"$contains": " "},
        )
        self.assertEqual(results, expected_results)

    @patch("app.infrastructure.vector_db.repository.Chroma")
    def test_check_document_exists_true(self, mock_chroma):
        # Arrange
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.get.return_value = {"ids": ["doc1", "doc2"]}
        mock_chroma.return_value = mock_chroma_instance

        repo = VectorDBRepository(
            self.settings,
            self.mock_chroma_client,
            self.mock_embeddings_client,
        )

        # Act
        exists = repo.check_document_exists({"titulo": "test_doc"})

        # Assert
        mock_chroma_instance.get.assert_called_once_with(where={"titulo": "test_doc"})
        self.assertTrue(exists)

    @patch("app.infrastructure.vector_db.repository.Chroma")
    def test_check_document_exists_false(self, mock_chroma):
        # Arrange
        mock_chroma_instance = MagicMock()
        mock_chroma_instance.get.return_value = {"ids": []}
        mock_chroma.return_value = mock_chroma_instance

        repo = VectorDBRepository(
            self.settings,
            self.mock_chroma_client,
            self.mock_embeddings_client,
        )

        # Act
        exists = repo.check_document_exists({"titulo": "nonexistent"})

        # Assert
        self.assertFalse(exists)

    @patch("app.infrastructure.vector_db.repository.Chroma")
    def test_as_retriever(self, mock_chroma):
        # Arrange
        mock_chroma_instance = MagicMock()
        mock_retriever = MagicMock()
        mock_chroma_instance.as_retriever.return_value = mock_retriever
        mock_chroma.return_value = mock_chroma_instance

        repo = VectorDBRepository(
            self.settings,
            self.mock_chroma_client,
            self.mock_embeddings_client,
        )

        # Act
        retriever = repo.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4},
        )

        # Assert
        mock_chroma_instance.as_retriever.assert_called_once_with(
            search_type="similarity",
            search_kwargs={"k": 4},
        )
        self.assertEqual(retriever, mock_retriever)


if __name__ == "__main__":
    unittest.main()
