from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.prompts import PromptTemplate
from langsmith import traceable

from app.core.config import Settings
from app.infrastructure.llm.client import LLMClient
from app.infrastructure.vector_db.repository import VectorDBRepository
from app.utils.load_prompt import load_prompt
from app.utils.logger import logger


class QAService:
    """Standard RAG service: retrieval + LLM answering."""

    # Default QA prompt
    DEFAULT_PROMPT = load_prompt("default_qa_prompt")

    def __init__(
        self,
        settings: Settings,
        llm_client: LLMClient,
        vdb_repository: VectorDBRepository,
    ) -> None:
        self._settings = settings
        self._llm = llm_client.client
        self._vdb_repo = vdb_repository

    @traceable
    def answer_question(
        self,
        query: str,
        document_type: str,
        k_results: int | None = None,
        custom_prompt: str | None = None,
    ) -> dict:
        """
        Answer question using standard RAG.

        Args:
            query: User question
            document_type: Filter documents by type (e.g., "documento-pdf")
            k_results: Number of chunks to retrieve (uses default if None)
            custom_prompt: Optional custom prompt template

        Returns:
            Dict with 'result' (answer) and 'source_documents' (list)
        """
        # Use defaults
        k_results = k_results or self._settings.default_k_results
        prompt_text = custom_prompt or self.DEFAULT_PROMPT

        logger.info(f"QA query: '{query[:50]}...' | doc_type={document_type} | k={k_results}")

        # 1. Create retriever with filters
        retriever = self._vdb_repo.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": k_results,
                "filter": {"tipo_documento": {"$eq": document_type}},
                "where_document": {"$contains": " "},
            },
        )

        # 2. Create QA prompt
        # This prompt will be used by the RetrievalQA chain (the one that uses the LLM)
        qa_prompt = PromptTemplate.from_template(template=prompt_text)

        # 3. Create RetrievalQA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=self._llm,
            retriever=retriever,
            return_source_documents=True,
            chain_type="stuff",  # TODO: Check with other chain types
            chain_type_kwargs={"prompt": qa_prompt},
        )

        # 4. Invoke chain
        # Is the actual question (query) answering step
        answer = qa_chain.invoke({"query": query})

        logger.info(f"QA answer generated: {len(answer['source_documents'])} sources")
        return answer
