import unittest
import uuid
from unittest.mock import MagicMock

import chromadb
from chromadb.config import Settings as ChromaSettings
from fastapi.testclient import TestClient
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding

from app.core.config import Settings
from app.core.dependencies import (
    get_db_session,
    get_document_service,
    get_ingestion_service,
    get_interaction_service,
    get_qa_service,
    get_rerank_service,
    get_vector_db_repository,
)
from app.infrastructure.vector_db.repository import VectorDBRepository
from main import app


TEXTS = [f"chunk number {i} about topic {i * 7}" for i in range(8)]
OFF_TOPIC_QUERY = "completely unrelated query zebra"


class TestSearchScoreRange(unittest.TestCase):
    """AC-17: /search scores are cosine similarities in [0, 1], over an in-memory Chroma."""

    def setUp(self):
        settings = Settings(default_k_results=4)
        settings.chromadb_collection = f"score-{uuid.uuid4().hex}"
        chroma_client = MagicMock()
        chroma_client.client = chromadb.EphemeralClient(
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        embeddings_client = MagicMock()
        embeddings_client.client = DeterministicFakeEmbedding(size=16)

        self.repo = VectorDBRepository(settings, chroma_client, embeddings_client)
        self.repo.add_documents(
            [
                Document(page_content=text, metadata={"titulo": "doc-a", "pagina": i})
                for i, text in enumerate(TEXTS)
            ]
        )

        self.document = MagicMock()
        document_service = MagicMock()
        document_service.get_by_title.return_value = self.document
        self.interaction_service = MagicMock()
        app.dependency_overrides[get_vector_db_repository] = lambda: self.repo
        app.dependency_overrides[get_qa_service] = lambda: MagicMock()
        app.dependency_overrides[get_rerank_service] = lambda: MagicMock()
        app.dependency_overrides[get_ingestion_service] = lambda: MagicMock()
        app.dependency_overrides[get_document_service] = lambda: document_service
        app.dependency_overrides[get_interaction_service] = lambda: self.interaction_service
        app.dependency_overrides[get_db_session] = lambda: MagicMock()
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_scores_are_bounded_ordered_and_logged(self):
        raw = self.repo.similarity_search_with_score(
            query=OFF_TOPIC_QUERY,
            k=len(TEXTS),
            metadata_filter={"titulo": {"$eq": "doc-a"}},
        )
        # Precondition: the clamp is exercised (raw distance above 1 would have caused a 500).
        self.assertTrue(any(distance > 1 for _, distance in raw))

        response = self.client.post(
            "/api/v1/documents/doc-a/search",
            json={"query": OFF_TOPIC_QUERY, "k_results": len(TEXTS), "metadata_filter": {}},
        )

        self.assertEqual(response.status_code, 200)
        scores = [r["score"] for r in response.json()["results"]]
        self.assertEqual(len(scores), len(TEXTS))
        self.assertTrue(all(0.0 <= s <= 1.0 for s in scores))
        self.assertEqual(scores, sorted(scores, reverse=True))
        logged = self.interaction_service.log_search.call_args.kwargs["results"]
        self.assertEqual([s for _, s in logged], scores)


if __name__ == "__main__":
    unittest.main()
