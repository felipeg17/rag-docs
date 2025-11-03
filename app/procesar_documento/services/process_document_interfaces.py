import pdb
import time

import dotenv

from app.procesar_documento.models.process_document_request import (
    ProcessDocumentRequest,
    SearchVectorDataBaseRequest,
)
from app.procesar_documento.services.process_document import ProcessDocument
from app.utils import logger


# Cargar variables de entorno
dotenv.load_dotenv()


class ProcessDocumentInterface:
    def __init__(self, query_id: str, input_data: ProcessDocumentRequest):
        self.query_id = query_id
        self.input_data = input_data
        self._start_time: float = 0.0
        self._finish_time: float = 0.0

    def process_document(self) -> bool:
        self._start_time = time.time()
        rag_document = ProcessDocument(
            query_id=self.query_id,
            document_chain=self.input_data.document_chain,
            document_title=self.input_data.title,
            document_type=self.input_data.document_type,
        )

        # * Cargar servicios
        logger.info("Cargando servicios")
        rag_document.load_services()

        # * Procesar documento
        logger.info("Procesando documento")
        rag_document.load_document()
        status_process = rag_document.process_document()
        self._finish_time = time.time()

        return status_process


class SearchVectorDataBaseInterface:
    def __init__(self, input_data: SearchVectorDataBaseRequest):
        self._input_data = input_data
        self._query_vdb_response = {"results": []}

    @property
    def query_vdb_response(self) -> dict:
        return self._query_vdb_response

    def search_vdb(self) -> None:
        rag_document = ProcessDocument(
            query_id="",
            document_title=self._input_data.title,
            document_type=self._input_data.document_type,
        )

        # * Cargar servicios
        logger.info("Cargando servicios")
        rag_document.load_services()

        # * Revisar existencia de documento
        if not rag_document.check_document_in_vdb(title=self._input_data.title):
            return

        vdb_result = rag_document.get_results_from_vdb_search(
            query=self._input_data.query,
            k_results=self._input_data.k_results,
            metadata_filter=self._input_data.metadata_filter,
        )
        self._parse_query_vdb_response(results=vdb_result)

    def _parse_query_vdb_response(self, results: list) -> None:
        if not results:
            return

        result_vdb = []
        for result in results:
            documentos = result[0].dict()
            score = result[1]
            result_vdb.append((documentos, score))
        # pdb.set_trace()

        self._query_vdb_response["results"] = result_vdb


class QueryQAChainInterface(SearchVectorDataBaseInterface):
    def __init__(self, input_data: SearchVectorDataBaseRequest):
        super().__init__(input_data=input_data)
        self._query_qa_chain_response = {
            "query": None,
            "result": None,
            "source_documents": [],
        }

    @property
    def query_qa_chain_response(self) -> dict:
        return self._query_qa_chain_response

    def query_qa_chain(self) -> None:
        rag_document = ProcessDocument(
            query_id="",
            document_title=self._input_data.title,
            document_type=self._input_data.document_type,
        )

        # * Cargar servicios
        logger.info("Cargando servicios")
        rag_document.load_services()

        # * Revisar existencia de documento
        if not rag_document.check_document_in_vdb(title=self._input_data.title):
            return

        # * Obtener documentos de la cadena de QA
        qa_result = rag_document.get_answer_from_rag_qa(
            query=self._input_data.query,
            k_results=self._input_data.k_results,
        )

        self._parse_query_qa_response(results=qa_result)

    def _parse_query_qa_response(self, results: dict) -> None:
        if not results:
            return

        self._query_qa_chain_response["query"] = results.get("query", self._input_data.query)
        self._query_qa_chain_response["result"] = results.get("result", None)
        source_documents = results.get("source_documents", [])
        self._query_qa_chain_response["source_documents"] = [
            element.dict() for element in source_documents
        ]


class QueryRerankChainInterface(QueryQAChainInterface):
    def __init__(self, input_data: SearchVectorDataBaseRequest):
        super().__init__(input_data=input_data)
        self._query_rerank_chain_response = {
            "query": self._input_data.query,
            "result": None,
        }

    @property
    def query_rerank_chain_response(self) -> dict:
        return self._query_rerank_chain_response

    def query_rerank_chain(self) -> None:
        rag_document = ProcessDocument(
            query_id="",
            document_title=self._input_data.title,
            document_type=self._input_data.document_type,
        )

        # * Cargar servicios
        logger.info("Cargando servicios")
        rag_document.load_services()

        # * Revisar existencia de documento
        if not rag_document.check_document_in_vdb(title=self._input_data.title):
            return

        # * Obtener documentos de la cadena de rerank
        rerank_result = rag_document.get_reranked_results(
            query=self._input_data.query,
            k_results=self._input_data.k_results,
        )

        # * Parsear respuesta
        self._query_rerank_chain_response["result"] = rerank_result
