from uuid import uuid4

from behave import when  # type: ignore
from behave.runner import Context  # type: ignore

from app.infrastructure.database.repositories.document_repository import DocumentRepository
from app.services.persistence.document_service import DocumentService


@when('a record of the document with title "{pdf_title}" is created in the persistent database')
def step_impl_create_document_record(context: Context, pdf_title: str) -> None:
    """Create a document record in the persistent database."""
    db_client = context.db_client
    session = db_client.get_session()
    doc_repo = DocumentRepository(session)
    doc_service = DocumentService(doc_repo)

    fake_content_str = f"Fake content for {pdf_title} - {uuid4()}"
    # convert to bytes
    fake_content = bytes(fake_content_str, encoding="utf-8")

    try:
        document = doc_service.create_document(
            title=pdf_title,
            document_type="documento-pdf",
            content=fake_content,
            file_size_bytes=len(fake_content),
            page_count=1,
        )
        session.commit()

    finally:
        session.close()

    context.created_document = document
    context.document_id = document.id
    context.pdf_title = pdf_title
