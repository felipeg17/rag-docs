import requests
from behave import then, when  # type: ignore
from behave.runner import Context  # type: ignore

from app.infrastructure.database.repositories.document_repository import DocumentRepository
from app.infrastructure.database.repositories.interaction_repository import QAInteractionRepository


@when("a question about the document is made")
def step_impl_define_question(context: Context) -> None:
    context.query = "What is the main usage of ROS?"


@then('a question is answered using the document with title "{pdf_title}" chunks as reference')
def step_impl_get_qa_chain(context: Context, pdf_title: str) -> None:
    """Verify the answer given by the qa chain"""
    payload = {
        "question": context.query,
        "strategy": "standard",
        "k_results": 1,
        "metadata_filter": {},
    }

    response = requests.post(
        f"{context.backend_url}/api/v1/documents/{pdf_title}/ask",
        json=payload,
        timeout=10,
    )

    assert response.status_code == 200, f"qa failed: {response.status_code}"

    upload_response = response.json()
    answer = upload_response.get("answer", "")
    assert len(answer) > 0, "No answer"

    sources = upload_response.get("source_documents", [])
    assert len(sources) > 0, "No results found in response"

    context.upload_response = upload_response
    context.answer = answer
    context.document_sources = sources
    context.document_id = upload_response.get("document_id")


@then("an interaction record is created in the persistent database")
def step_impl_create_interaction_persistent_db(context: Context) -> None:
    status_value = context.upload_response.get("status")
    assert status_value is not None, "No status in upload response"


@then(
    "the interaction record attached to the document should be retrievable from the persistent database"
)
def step_impl_retrieve_document_interaction_persistent_db(context: Context) -> None:
    db_client = context.db_client
    session = db_client.get_session()
    try:
        qa_interaction_repo = QAInteractionRepository(session)
        document_repo = DocumentRepository(session)
        document = document_repo.get_by_title(context.pdf_title)
        assert document is not None, "Document not found in persistent database"
        interactions = qa_interaction_repo.get_by_document_id(document.id)
        # Get the most recent interaction
        interaction = interactions[0] if interactions else None
        assert interaction is not None, "Interaction not found in persistent database"
    finally:
        session.close()
