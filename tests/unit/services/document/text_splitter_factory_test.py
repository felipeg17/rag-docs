import unittest
from unittest.mock import MagicMock

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker

from app.core.config import Settings
from app.services.document.text_splitter import TextSplitterFactory


class TestTextSplitterFactory(unittest.TestCase):
    def setUp(self):
        # Mock Settings with default values
        self.settings = Settings(
            default_chunk_size=800,
            default_chunk_overlap=50,
        )

        # Mock embeddings client
        self.mock_embeddings = MagicMock()

        # Create factory instance
        self.factory = TextSplitterFactory(self.settings, self.mock_embeddings)

    def test_create_recursive_splitter_returns_correct_type(self):
        # Act
        splitter = self.factory.create_splitter(method="recursive")

        # Assert
        self.assertIsInstance(splitter, RecursiveCharacterTextSplitter)
        self.assertEqual(splitter._chunk_size, self.settings.default_chunk_size)
        self.assertEqual(splitter._chunk_overlap, self.settings.default_chunk_overlap)

    def test_create_recursive_splitter_with_custom_parameters(self):
        # Arrange
        custom_chunk_size = 1000
        custom_overlap = 100

        # Act
        splitter = self.factory.create_splitter(
            method="recursive", chunk_size=custom_chunk_size, chunk_overlap=custom_overlap
        )

        # Assert
        self.assertEqual(splitter._chunk_size, custom_chunk_size)
        self.assertEqual(splitter._chunk_overlap, custom_overlap)

    def test_create_semantic_splitter_returns_correct_type(self):
        # Act
        splitter = self.factory.create_splitter(method="semantic")

        # Assert
        self.assertIsInstance(splitter, SemanticChunker)
        self.assertEqual(splitter.embeddings, self.mock_embeddings)
        self.assertEqual(splitter.breakpoint_threshold_type, "gradient")

    def test_create_splitter_default_method_is_recursive(self):
        # Act
        splitter = self.factory.create_splitter()

        # Assert
        self.assertIsInstance(splitter, RecursiveCharacterTextSplitter)


if __name__ == "__main__":
    unittest.main()
