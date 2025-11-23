from langchain.prompts import ChatPromptTemplate
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_cohere import CohereRerank
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langsmith import traceable

from app.core.config import Settings
from app.infrastructure.llm.client import LLMClient
from app.infrastructure.vector_db.repository import VectorDBRepository
from app.utils.load_prompt import load_prompt
from app.utils.logger import logger


class RerankService:
    """RAG service with Cohere reranking: retrieval -> rerank -> LLM."""

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
        rerank_top_n: int | None = None,
        custom_prompt: str | None = None,
    ) -> str:
        """
        Answer question using RAG with Cohere reranking.

        Args:
            query: User question
            document_type: Filter documents by type (e.g., "documento-pdf")
            k_results: Number of chunks to retrieve (uses default if None)
            rerank_top_n: Number of top chunks after reranking (uses default if None)
            custom_prompt: Optional custom prompt template

        Returns:
            Answer string
        """
        # Use defaults
        k_results = k_results or self._settings.default_k_results
        rerank_top_n = rerank_top_n or self._settings.default_rerank_top_n
        prompt_text = custom_prompt or self.DEFAULT_PROMPT

        logger.info(
            f"Rerank QA query: '{query[:50]}...' | doc_type={document_type} | "
            f"k={k_results} | rerank_top_n={rerank_top_n}"
        )

        # 1. Create base retriever with filters
        base_retriever = self._vdb_repo.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": k_results,
                "filter": {"tipo-documento": {"$eq": document_type}},
                "where_document": {"$contains": " "},
            },
        )

        # 2. Create Cohere reranker
        compressor = CohereRerank(
            top_n=rerank_top_n,
            model=self._settings.cohere_model,
            cohere_api_key=self._settings.cohere_api_key,
        )

        # 3. Wrap retriever with compression
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=base_retriever,
        )

        # 4. Create QA prompt
        qa_prompt = ChatPromptTemplate.from_template(template=prompt_text)

        # 5. Build LCEL chain
        setup_and_retrieval = RunnableParallel(
            {"question": RunnablePassthrough(), "context": compression_retriever}
        )

        chain = setup_and_retrieval | qa_prompt | self._llm | StrOutputParser()

        # 6. Invoke chain
        answer = chain.invoke(query)

        logger.info("Rerank QA answer generated")
        return answer
