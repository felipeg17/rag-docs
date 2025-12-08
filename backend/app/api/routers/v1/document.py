from typing import Annotated
import uuid

from fastapi import APIRouter, HTTPException, Path, status
from fastapi.responses import JSONResponse

from app.core.dependencies import IngestionServiceDep, QAServiceDep, RerankServiceDep, VectorDBDep
from app.models.requests.document_request import DocumentIngestRequest
from app.models.requests.search_request import DocumentSearchRequest, QuestionRequest
from app.models.responses.document_response import DocumentIngestResponse
from app.models.responses.qa_response import QuestionAnswerResponse, SourceDocument
from app.models.responses.search_response import DocumentSearchResponse, SearchResultItem
from app.utils import logger


router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "",
    response_model=DocumentIngestResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Document created successfully"},
        200: {"description": "Document already exists (updated)"},
        400: {"description": "Invalid request"},
        500: {"description": "Internal server error"},
    },
)
async def ingest_document(
    request: DocumentIngestRequest, ingestion_service: IngestionServiceDep, vdb_repo: VectorDBDep
):
    try:
        # Check if document already exists
        document_exists = vdb_repo.check_document_exists({"titulo": request.title})

        if document_exists:
            # TODO: When have persistant storage for documents retrieve document_id
            document_id = str(uuid.uuid4())

        # Process document if not present
        if not document_exists:
            document_id = str(uuid.uuid4())
            logger.info(f"Ingesting document: {request.title} (document_id={document_id})")
            # ? What to do when it resurns False?
            result_process = ingestion_service.ingest_document(
                base64_content=request.document_content,
                title=request.title,
                document_type=request.document_type or "documento-pdf",
                splitting_method="recursive",  # TODO: Make this configurable
            )

        response_data = DocumentIngestResponse(
            document_id=document_id,
            title=request.title,
            status="updated" if document_exists else "created",
            message=f"Document '{'updated' if document_exists else 'created'}' successfully",
        )

        response_status = status.HTTP_200_OK if document_exists else status.HTTP_201_CREATED

        return JSONResponse(
            status_code=response_status,
            content=response_data.model_dump(),
            headers={"Location": f"/api/v1/documents/{document_id}"}
            if not document_exists
            else None,
        )

    except Exception as e:
        error_message = f"Error ingesting document: {type(e).__name__} - {str(e)}"
        logger.error(error_message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message,
        )


@router.post(
    "/{document_id}/search",
    response_model=DocumentSearchResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Search completed successfully"},
        404: {"description": "Document not found"},
        500: {"description": "Internal server error"},
    },
)
async def search_document(
    document_id: Annotated[str, Path(description="Document title")],
    request: DocumentSearchRequest,
    vdb_repo: VectorDBDep,
):
    try:
        # Check if document exists
        if not vdb_repo.check_document_exists({"titulo": document_id}):
            return {"results": []}

        # Perform similarity search
        vdb_results = vdb_repo.similarity_search_with_score(
            query=request.query,
            k=request.k_results,
            metadata_filter=request.metadata_filter,
        )

        # Parse results (Document, score) tuples
        search_items = [
            SearchResultItem(
                content=doc.page_content,
                score=float(score),
                metadata=doc.metadata,
            )
            for doc, score in vdb_results
        ]

        return DocumentSearchResponse(
            query=request.query,
            results=search_items,
            total_results=len(search_items),
        )

    except Exception as e:
        error_message = f"Error searching document: {type(e).__name__} - {str(e)}"
        logger.error(error_message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message,
        )


@router.post(
    "/{document_id}/ask",
    response_model=QuestionAnswerResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Question answered successfully"},
        404: {"description": "Document not found"},
        500: {"description": "Internal server error"},
    },
)
async def ask_question(
    document_id: Annotated[str, Path(description="Document title")],
    request: QuestionRequest,
    qa_service: QAServiceDep,
    rerank_service: RerankServiceDep,
    vdb_repo: VectorDBDep,
):
    try:
        # Check if document exists
        if not vdb_repo.check_document_exists({"titulo": document_id}):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{document_id}' not found"
            )

        # Select service based on strategy
        if request.strategy == "rerank":
            # Rerank strategy - returns only the answer
            answer = rerank_service.answer_question(
                query=request.question,
                document_type="documento-pdf",  # TODO: remove the hardcoded
                k_results=request.k_results,
            )

            return QuestionAnswerResponse(
                question=request.question,
                answer=answer,
                document_id=document_id,
                strategy="rerank",
                source_documents=[],  # Rerank service doesn't return sources
            )
        else:
            # Standard strategy - returns answer + sources
            qa_result = qa_service.answer_question(
                query=request.question,
                document_type="documento-pdf",  # TODO: remove the hardcoded
                k_results=request.k_results,
            )

            source_docs = [
                SourceDocument(
                    page_content=doc.page_content,
                    metadata=doc.metadata,
                    score=None,  # Standard QA doesn't provide scores
                )
                for doc in qa_result.get("source_documents", [])
            ]

            return QuestionAnswerResponse(
                question=request.question,
                answer=qa_result.get("result"),
                document_id=document_id,
                strategy="standard",
                source_documents=source_docs,
            )

    except HTTPException:
        raise
    except Exception as e:
        error_message = f"Error answering question: {type(e).__name__} - {str(e)}"
        logger.error(error_message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message,
        )
