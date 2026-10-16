import unittest
from unittest.mock import MagicMock, patch

from langchain.schema import Document
from langchain_postgres.v2.indexes import DistanceStrategy

from app.core.config import Settings
from app.infrastructure.vector_db.pgvector_repository import PGVectorDBRepository


class TestPGVectorDBRepository(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(default_k_results=4)
        self.mock_client = MagicMock()
        self.mock_embeddings_client = MagicMock()

    def _make_repo(self, mock_store_cls, mock_engine_cls):
        self.mock_store = MagicMock()
        mock_store_cls.create_sync.return_value = self.mock_store
        return PGVectorDBRepository(self.settings, self.mock_client, self.mock_embeddings_client)

    @patch("app.infrastructure.vector_db.pgvector_repository.PGEngine")
    @patch("app.infrastructure.vector_db.pgvector_repository.PGVectorStore")
    def test_supplied_filter_is_forwarded_unchanged(self, mock_store_cls, mock_engine_cls):
        repo = self._make_repo(mock_store_cls, mock_engine_cls)
        scoped = {"titulo": {"$eq": "doc-a"}}

        repo.similarity_search_with_score(query="q", k=2, metadata_filter=scoped)

        self.mock_store.similarity_search_with_score.assert_called_once_with(
            query="q", k=2, filter=scoped, where_document=None
        )

    @patch("app.infrastructure.vector_db.pgvector_repository.PGEngine")
    @patch("app.infrastructure.vector_db.pgvector_repository.PGVectorStore")
    def test_none_filter_uses_default(self, mock_store_cls, mock_engine_cls):
        repo = self._make_repo(mock_store_cls, mock_engine_cls)

        repo.similarity_search_with_score(query="q", k=2)

        self.mock_store.similarity_search_with_score.assert_called_once_with(
            query="q",
            k=2,
            filter={"tipo_documento": "documento-pdf"},
            where_document=None,
        )


if __name__ == "__main__":
    unittest.main()

    @patch("app.infrastructure.vector_db.pgvector_repository.PGEngine")
    @patch("app.infrastructure.vector_db.pgvector_repository.PGVectorStore")
    def test_cosine_distance_strategy_is_pinned(self, mock_store_cls, mock_engine_cls):
        self._make_repo(mock_store_cls, mock_engine_cls)

        kwargs = mock_store_cls.create_sync.call_args.kwargs
        self.assertEqual(kwargs["distance_strategy"], DistanceStrategy.COSINE_DISTANCE)

    @patch("app.infrastructure.vector_db.pgvector_repository.PGEngine")
    @patch("app.infrastructure.vector_db.pgvector_repository.PGVectorStore")
    def test_relevance_scores_convert_distance_to_similarity(self, mock_store_cls, mock_engine_cls):
        repo = self._make_repo(mock_store_cls, mock_engine_cls)
        docs = [Document(page_content="a", metadata={}), Document(page_content="b", metadata={})]
        self.mock_store.similarity_search_with_score.return_value = [
            (docs[0], 0.3),
            (docs[1], 1.708),
        ]
        scoped = {"titulo": {"$eq": "doc-a"}}

        results = repo.similarity_search_with_relevance_scores(
            query="q", k=2, metadata_filter=scoped
        )

        self.assertEqual([d for d, _ in results], docs)
        self.assertAlmostEqual(results[0][1], 0.7)
        self.assertAlmostEqual(results[1][1], 0.0)
        self.mock_store.similarity_search_with_score.assert_called_once_with(
            query="q", k=2, filter=scoped, where_document=None
        )
