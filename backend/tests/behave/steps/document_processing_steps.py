import base64
import time
from pathlib import Path

import requests
from behave import given, then, when  # type: ignore
from behave.runner import Context  # type: ignore

from app.core.config import VectorDBType, settings
from app.core.dependencies import get_chroma_client, get_db_client, get_pgvector_client
from app.infrastructure.database.repositories.document_repository import DocumentRepository


@given("the persistent database is running")
def step_impl_persistent_db_running(context: Context) -> None:
    db_client = get_db_client()
    if not db_client.heartbeat():
        raise AssertionError("PostgreSQL not accessible through backend")

    context.db_client = db_client


@given("the vector database is running")
def step_impl_vector_db_running(context: Context) -> None:
    if settings.vector_db_type == VectorDBType.PGVECTOR:
        if not get_pgvector_client().heartbeat():
            raise AssertionError("PGVector not accessible through backend")
    else:
        if not get_chroma_client().heartbeat():
            raise AssertionError("ChromaDB not accessible through backend")


@given("the backend is running")
def step_impl_backend_running(context: Context) -> None:
    max_retries = 5
    for _ in range(max_retries):
        try:
            response = requests.get(f"{context.backend_url}/health", timeout=1)
            if response.status_code == 200:
                return
        except requests.exceptions.RequestException:
            time.sleep(0.5)

    raise AssertionError("Backend not accessible")


@when('a pdf document with title "{pdf_title}" is uploaded')
def step_impl_upload_document_vector_db(context: Context, pdf_title: str) -> None:
    tests_path = Path(__file__).parent.parent.parent
    pdf_path = tests_path / "fixtures" / "data" / "ros-intro.pdf"
    with open(pdf_path, "rb") as f:
        test_pdf_base64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "title": pdf_title,
        "document_type": "documento-pdf",
        "document_content": test_pdf_base64,
    }

    response = requests.post(
        f"{context.backend_url}/api/v1/documents",
        json=payload,
        timeout=60,
    )

    assert response.status_code in [200, 201], f"Document upload failed: {response.status_code}"

    context.upload_response = response.json()
    context.document_id = context.upload_response.get("document_id")
    context.pdf_title = context.upload_response.get("title")


@then("a document record is created in the persistent database")
def step_impl_create_document_persistent_db(context: Context) -> None:
    # status=True means newly created (201), status=False means already exists (200)
    status_value = context.upload_response.get("status")
    assert status_value is not None, "No status in upload response"


@then('document with title "{pdf_title}" is created in the vector database')
def step_impl_create_document_vector_db(context: Context, pdf_title: str) -> None:
    # status=True means newly created (201), status=False means already exists (200)
    status_value = context.upload_response.get("status")
    assert status_value is not None, "No status in upload response"


@then("the document record should be retrievable from the persistent database")
def step_impl_retrieve_document_persistent_db(context: Context) -> None:
    db_client = context.db_client
    session = db_client.get_session()
    try:
        doc_repo = DocumentRepository(session)
        document = doc_repo.get_by_id(context.document_id)
        assert document is not None, "Document not found in persistent database"
        assert document.title == context.pdf_title
    finally:
        session.close()


@then('the document with title "{pdf_title}" should be retrievable from the vector database')
def step_impl_retrieve_document_from_vdb(context: Context, pdf_title: str) -> None:
    """Verify document can be retrieved from vector database."""
    payload = {
        "query": "What is ROS?",
        "k_results": 1,
        "metadata_filter": {},
    }

    response = requests.post(
        f"{context.backend_url}/api/v1/documents/{pdf_title}/search",
        json=payload,
        timeout=10,
    )

    assert response.status_code == 200, f"VDB search failed: {response.status_code}"

    results = response.json().get("results", [])
    assert len(results) > 0, "No results found in vector database"

    context.vdb_results = results
