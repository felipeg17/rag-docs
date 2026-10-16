import unittest
import uuid
from unittest.mock import MagicMock

import chromadb
from chromadb.config import Settings as ChromaSettings
from fastapi.testclient import TestClient
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models.fake import FakeListLLM

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
from app.services.rag.qa_service import QAService
from main import app


# Identical text keeps the cosine distance at 0, so the similarity score is 1.
SHARED_TEXT = "alpha text shared by both"


class TestDocumentScopingEndToEnd(unittest.TestCase):
    """Real VectorDBRepository + QAService over in-memory Chroma; no network, no live LLM."""

    def setUp(self):
        settings = Settings(default_k_results=4)
        collection = f"scoping-{uuid.uuid4().hex}"
        chroma = chromadb.EphemeralClient(settings=ChromaSettings(anonymized_telemetry=False))
        chroma_client = MagicMock()
        chroma_client.client = chroma
        embeddings_client = MagicMock()
        embeddings_client.client = DeterministicFakeEmbedding(size=16)
        settings.chromadb_collection = collection

        self.repo = VectorDBRepository(settings, chroma_client, embeddings_client)
        self.repo.add_documents(
            [
                Document(
                    page_content=SHARED_TEXT,
                    metadata={"titulo": "doc-a", "tipo_documento": "custom-type", "pagina": 0},
                ),
                Document(
                    page_content=SHARED_TEXT,
                    metadata={"titulo": "doc-b", "tipo_documento": "documento-pdf", "pagina": 0},
                ),
            ]
        )

        llm_client = MagicMock()
        llm_client.client = FakeListLLM(responses=["fake answer"])
        qa_service = QAService(settings, llm_client, self.repo)

        document_service = MagicMock()
        document_service.get_by_title.return_value = None
        app.dependency_overrides[get_vector_db_repository] = lambda: self.repo
        app.dependency_overrides[get_qa_service] = lambda: qa_service
        app.dependency_overrides[get_rerank_service] = lambda: MagicMock()
        app.dependency_overrides[get_ingestion_service] = lambda: MagicMock()
        app.dependency_overrides[get_document_service] = lambda: document_service
        app.dependency_overrides[get_interaction_service] = lambda: MagicMock()
        app.dependency_overrides[get_db_session] = lambda: MagicMock()
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_search_returns_only_requested_document_with_custom_type(self):
        payload = {"query": SHARED_TEXT, "k_results": 4, "metadata_filter": {}}

        response = self.client.post("/api/v1/documents/doc-a/search", json=payload)

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual({r["metadata"]["titulo"] for r in results}, {"doc-a"})

    def test_ask_returns_only_requested_document_sources_with_custom_type(self):
        payload = {"question": SHARED_TEXT, "strategy": "standard", "k_results": 4}

        response = self.client.post("/api/v1/documents/doc-a/ask", json=payload)

        self.assertEqual(response.status_code, 200)
        sources = response.json()["source_documents"]
        self.assertGreaterEqual(len(sources), 1)
        self.assertEqual({s["metadata"]["titulo"] for s in sources}, {"doc-a"})


if __name__ == "__main__":
    unittest.main()
