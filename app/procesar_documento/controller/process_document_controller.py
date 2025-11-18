import uuid

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.procesar_documento.models.process_document_request import (
    ProcessDocumentRequest,
    SearchVectorDataBaseRequest,
)
from app.procesar_documento.services.process_document_handlers import (
    ProcessDocumentHandler,
    QueryQAChainHandler,
    QueryRerankChainHandler,
    SearchVectorDataBaseHandler,
)
from app.utils import logger


router = APIRouter()


@router.post("/api/v1/documento")
async def process_document(request: ProcessDocumentRequest):
    try:
        query_id = str(uuid.uuid4())
        process_document_handler = ProcessDocumentHandler(query_id=query_id, input_data=request)
        result_process = process_document_handler.process_document()

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


@router.post("/api/v1/busqueda_bdv", status_code=status.HTTP_200_OK)
async def search_vdb(request: SearchVectorDataBaseRequest):
    try:
        search_vdb_handler = SearchVectorDataBaseHandler(input_data=request)
        search_vdb_handler.search_vdb()
        return search_vdb_handler.query_vdb_response
    except Exception as e:
        error_message = f"Error en búsqueda: {type(e).__name__} - {str(e)}"
        logger.error(error_message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message,
        )


@router.post("/api/v1/qa", status_code=status.HTTP_200_OK)
async def query_qa_chain(request: SearchVectorDataBaseRequest):
    try:
        query_qa_chain_handler = QueryQAChainHandler(input_data=request)
        query_qa_chain_handler.query_qa_chain()
        return query_qa_chain_handler.query_qa_chain_response
    except Exception as e:
        error_message = f"Error en cadena QA: {type(e).__name__} - {str(e)}"
        logger.error(error_message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message,
        )


@router.post("/api/v1/qa_ranked", status_code=status.HTTP_200_OK)
async def query_reranked_chain(request: SearchVectorDataBaseRequest):
    try:
        query_rerank_chain_handler = QueryRerankChainHandler(input_data=request)
        query_rerank_chain_handler.query_rerank_chain()
        return query_rerank_chain_handler.query_rerank_chain_response
    except Exception as e:
        error_message = f"Error en cadena rankeada: {type(e).__name__} - {str(e)}"
        logger.error(error_message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message,
        )
