from behave import then  # type: ignore
from behave.runner import Context  # type: ignore
import requests


@then(
    'a question is answered using the document with title "{pdf_title}" '
    "filtered chunks as reference"
)
def step_impl_get_qa_ranked(context: Context, pdf_title: str) -> None:
    """Verify the answer given by the qa chain"""
    payload = {
        "title": pdf_title,
        "document_type": "documento-pdf",
        "query": context.query,
        "k_results": 4,
        "metadata_filter": {},
    }

    response = requests.post(
        f"{context.backend_url}/rag-docs/api/v1/qa_ranked",
        json=payload,
        timeout=10,
    )

    assert response.status_code == 200, f"qa ranked failed: {response.status_code}"

    answer = response.json().get("result", "")
    assert len(answer) > 0, "No answer"

    context.answer = answer
