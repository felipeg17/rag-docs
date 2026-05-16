from behave import then, when  # type: ignore
from behave.runner import Context  # type: ignore
import requests


@when("a question about the document is made")
def step_impl_define_question(context: Context) -> None:
    context.query = "What is the main usage of ROS?"


@then('a question is answered using the document with title "{pdf_title}" chunks as reference')
def step_impl_get_qa_chain(context: Context, pdf_title: str) -> None:
    payload = {
        "question": context.query,
        "k_results": 2,
        "strategy": "standard",
    }

    response = requests.post(
        f"{context.backend_url}/api/v1/documents/{pdf_title}/ask",
        json=payload,
        timeout=120,
    )

    assert response.status_code == 200, f"qa failed: {response.status_code} - {response.text}"

    answer = response.json().get("answer", "")
    assert len(answer) > 0, "No answer"

    sources = response.json().get("source_documents", [])
    assert len(sources) > 0, "No source documents in response"

    context.answer = answer
    context.document_sources = sources
