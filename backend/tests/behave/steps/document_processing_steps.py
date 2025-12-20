import base64
import time
from pathlib import Path

import requests
from behave import given, then, when  # type: ignore
from behave.runner import Context  # type: ignore


@given("the vector database is running")
def step_impl_vector_db_running(context: Context) -> None:
    max_retries = 5
    for _ in range(max_retries):
        try:
            response = requests.get(f"{context.vectordb_url}/api/v2/healthcheck", timeout=1)
            if response.status_code == 200:
                return
        except requests.exceptions.RequestException:
            time.sleep(0.5)

    raise AssertionError("Vector database not accessible through backend")


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
    context.pdf_title = pdf_title


@then('document with title "{pdf_title}" is created in the vector database')
def step_impl_create_document_vector_db(context: Context, pdf_title: str) -> None:
    # status=True means newly created (201), status=False means already exists (200)
    status_value = context.upload_response.get("status")
    assert status_value is not None, "No status in upload response"


@then('the document with title "{pdf_title}" is retrievable from the vector database')
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
