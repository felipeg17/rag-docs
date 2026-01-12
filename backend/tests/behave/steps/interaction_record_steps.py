from uuid import UUID, uuid4

from behave import then, when  # type: ignore
from behave.runner import Context  # type: ignore

from app.infrastructure.database.repositories.interaction_repository import (
    QAInteractionRepository,
    SearchInteractionRepository,
)
from app.services.persistence.interaction_service import InteractionService


@when("a record of an interaction is created in the persistent database")
def step_impl_create_interaction_record(context: Context) -> None:
    """Create a interaction record (log_qa) in the persistent database."""
    db_client = context.db_client
    session = db_client.get_session()
    interaction_repo = QAInteractionRepository(session)
    search_repo = SearchInteractionRepository(session)
    interaction_service = InteractionService(search_repo, interaction_repo)
    document_id = str(uuid4())
    try:
        interaction = interaction_service.log_qa(
            document_id=UUID(document_id),
            question="What is the main usage of ROS?",
            answer="ROS is mainly used for robotics applications.",
            strategy="standard",
            k_results=1,
            llm_model="gpt-4",
            execution_time_ms=150,
        )
        session.commit()

    finally:
        session.close()

    assert interaction is not None, "Failed to create interaction record in the database"
    assert interaction.id is not None, "Interaction record ID is None"
    context.interaction_id = str(interaction.id)


@then("the interaction record should be retrievable from the persistent database")
def step_impl_retrieve_interaction_persistent_db(context: Context) -> None:
    db_client = context.db_client
    session = db_client.get_session()
    try:
        qa_interaction_repo = QAInteractionRepository(session)
        interaction = qa_interaction_repo.get_by_id(UUID(context.interaction_id))
        assert interaction is not None, (
            f"Interaction id {context.interaction_id} not found in persistent database"
        )
    finally:
        session.close()
