import requests
from behave import then  # type: ignore
from behave.runner import Context  # type: ignore


@then(
    'a question is answered using the document with title "{pdf_title}" '
    "filtered chunks as reference"
)
def step_impl_get_qa_ranked(context: Context, pdf_title: str) -> None:
    """Verify the answer given by the qa chain"""
    payload = {
        "question": context.query,
        "strategy": "rerank",
        "k_results": 4,
        "metadata_filter": {},
    }

    response = requests.post(
        f"{context.backend_url}/api/v1/documents/{pdf_title}/ask",
        json=payload,
        timeout=10,
    )

    assert response.status_code == 200, f"qa ranked failed: {response.status_code}"

    answer = response.json().get("answer", "")
    assert len(answer) > 0, "No answer"

    context.answer = answer
