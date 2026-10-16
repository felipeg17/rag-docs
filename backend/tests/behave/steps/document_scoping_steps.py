import base64
from pathlib import Path

import requests
from behave import given, then, when  # type: ignore
from behave.runner import Context  # type: ignore


_TESTS_PATH = Path(__file__).parent.parent.parent
_PDF_DIRS = [_TESTS_PATH / "behave" / "data", _TESTS_PATH / "fixtures" / "data"]


def _find_pdf(filename: str) -> Path:
    for directory in _PDF_DIRS:
        candidate = directory / filename
        if candidate.exists():
            return candidate
    raise AssertionError(f"Fixture {filename} not found in {_PDF_DIRS}")


@given('the pdf "{filename}" is ingested with title "{title}"')
def step_impl_ingest_pdf(context: Context, filename: str, title: str) -> None:
    content = base64.b64encode(_find_pdf(filename).read_bytes()).decode("utf-8")
    payload = {
        "title": title,
        "document_type": "documento-pdf",
        "document_content": content,
    }
    response = requests.post(f"{context.backend_url}/api/v1/documents", json=payload, timeout=120)
    assert response.status_code in [200, 201], (
        f"Upload of {title} failed: {response.status_code} {response.text[:200]}"
    )


@when('a search on "{title}" is made with "{query}"')
def step_impl_search(context: Context, title: str, query: str) -> None:
    payload = {"query": query, "k_results": 4, "metadata_filter": {}}
    response = requests.post(
        f"{context.backend_url}/api/v1/documents/{title}/search", json=payload, timeout=30
    )
    assert response.status_code == 200, (
        f"search failed: {response.status_code} {response.text[:200]}"
    )
    context.search_results = response.json().get("results", [])


@then("at least one result is returned")
def step_impl_has_results(context: Context) -> None:
    assert len(context.search_results) > 0, "No search results returned"


@then('every result belongs to the document "{title}"')
def step_impl_results_scoped(context: Context, title: str) -> None:
    titles = [r.get("metadata", {}).get("titulo") for r in context.search_results]
    assert all(t == title for t in titles), f"Results from other documents: {titles}"


@when('a standard question is asked on "{title}" with "{question}"')
def step_impl_ask(context: Context, title: str, question: str) -> None:
    payload = {"question": question, "strategy": "standard", "k_results": 4, "metadata_filter": {}}
    response = requests.post(
        f"{context.backend_url}/api/v1/documents/{title}/ask", json=payload, timeout=180
    )
    assert response.status_code == 200, f"ask failed: {response.status_code} {response.text[:200]}"
    context.ask_sources = response.json().get("source_documents", [])


@then('every source document belongs to the document "{title}"')
def step_impl_sources_scoped(context: Context, title: str) -> None:
    titles = [s.get("metadata", {}).get("titulo") for s in context.ask_sources]
    assert titles, "No source documents returned"
    assert all(t == title for t in titles), f"Sources from other documents: {titles}"
