import uuid

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.dependencies import IngestionServiceDep, QAServiceDep, RerankServiceDep, VectorDBDep
from app.models.process_document_request import ProcessDocumentRequest, SearchVectorDataBaseRequest
from app.utils import logger


router = APIRouter()


@router.post("/api/v1/document")
async def process_document(
    request: ProcessDocumentRequest,
    ingestion_service: IngestionServiceDep,
):
    try:
        query_id = str(uuid.uuid4())
        logger.info(f"Processing document: {request.title} (query_id={query_id})")

        result_process = ingestion_service.ingest_document(
            base64_content=request.document_content,
            title=request.title,
            document_type=request.document_type or "documento-pdf",
            splitting_method="recursive",  # TODO: Make this configurable
        )

        response_status = status.HTTP_201_CREATED if result_process else status.HTTP_200_OK

        return JSONResponse(
            status_code=response_status,
            content={"query_id": query_id, "status": result_process},
        )

    except Exception as e:
        error_message = f"Error procesando documento: {type(e).__name__} - {str(e)}"
        logger.error(error_message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message,
        )


@router.post("/api/v1/vdb_result", status_code=status.HTTP_200_OK)
async def search_vdb(
    request: SearchVectorDataBaseRequest,
    vdb_repo: VectorDBDep,
):
    try:
        # Check if document exists
        if not vdb_repo.check_document_exists({"titulo": request.title}):
            return {"results": []}

        # Perform similarity search
        vdb_results = vdb_repo.similarity_search_with_score(
            query=request.query,
            k=request.k_results,
            filter=request.metadata_filter,
        )

        # Parse results (Document, score) tuples
        parsed_results = [(doc.model_dump(), score) for doc, score in vdb_results]

        return {"results": parsed_results}

    except Exception as e:
        error_message = f"Error en búsqueda: {type(e).__name__} - {str(e)}"
        logger.error(error_message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message,
        )


@router.post("/api/v1/qa", status_code=status.HTTP_200_OK)
async def query_qa_chain(
    request: SearchVectorDataBaseRequest,
    qa_service: QAServiceDep,
    vdb_repo: VectorDBDep,
):
    try:
        # Check if document exists
        if not vdb_repo.check_document_exists({"titulo": request.title}):
            return {
                "query": request.query,
                "result": None,
                "source_documents": [],
            }

        # Get answer from QA service
        qa_result = qa_service.answer_question(
            query=request.query,
            document_type=request.document_type or "documento-pdf",
            k_results=request.k_results,
        )

        # Parse response (convert Documents to dicts)
        return {
            "query": qa_result.get("query", request.query),
            "result": qa_result.get("result"),
            "source_documents": [doc.model_dump() for doc in qa_result.get("source_documents", [])],
        }

    except Exception as e:
        error_message = f"Error en cadena QA: {type(e).__name__} - {str(e)}"
        logger.error(error_message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message,
        )


@router.post("/api/v1/qa_ranked", status_code=status.HTTP_200_OK)
async def query_reranked_chain(
    request: SearchVectorDataBaseRequest,
    rerank_service: RerankServiceDep,
    vdb_repo: VectorDBDep,
):
    try:
        # Check if document exists
        if not vdb_repo.check_document_exists({"titulo": request.title}):
            return {
                "query": request.query,
                "result": None,
            }

        # Get answer from Rerank service
        answer = rerank_service.answer_question(
            query=request.query,
            document_type=request.document_type or "documento-pdf",
            k_results=request.k_results,
        )

        return {
            "query": request.query,
            "result": answer,
        }

    except Exception as e:
        error_message = f"Error en cadena rankeada: {type(e).__name__} - {str(e)}"
        logger.error(error_message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message,
        )
