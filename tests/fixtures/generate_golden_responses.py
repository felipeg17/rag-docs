import base64
from datetime import datetime
import json
from pathlib import Path
import sys


# Add project root to Python path to enable imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from langchain_cohere import CohereRerank  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.dependencies import (  # noqa: E402
    get_chroma_client,
    get_embeddings_client,
    get_llm_client,
    get_vector_db_repository,
)


# Test configuration
TEST_DOCUMENT_TITLE = "ros-intro"
TEST_DOCUMENT_TYPE = "documento-pdf"
TEST_QUERY = "What is ROS and what is it used for?"
TEST_K_RESULTS = 4
TEST_RERANK_TOP_N = 3

# Output directory
GOLDEN_DIR = Path(__file__).parent / "golden_responses"
DOCUMENTS_DIR = Path(__file__).parent.parent.parent / "documents"


def save_golden_response(filename: str, data: dict) -> None:
    """Save golden response to JSON file with pretty formatting."""
    output_path = GOLDEN_DIR / filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved: {filename}")


def record_current_settings() -> dict:
    """Record current settings for reproducibility."""
    return {
        "openai_model": settings.openai_model,
        "openai_temperature": settings.openai_temperature,
        "openai_max_tokens": settings.openai_max_tokens,
        "openai_top_p": settings.openai_top_p,
        "embeddings_model": settings.embeddings_model,
        "chromadb_collection": settings.chromadb_collection,
        "default_chunk_size": settings.default_chunk_size,
        "default_chunk_overlap": settings.default_chunk_overlap,
        "default_k_results": settings.default_k_results,
        "default_rerank_top_n": settings.default_rerank_top_n,
        "cohere_model": settings.cohere_model,
    }


def generate_settings_snapshot() -> None:
    """Generate settings snapshot for golden response validation."""
    print("\nGenerating settings snapshot...")

    golden_response = {
        "description": "Settings snapshot for golden responses reproducibility",
        "generated_at": datetime.now().isoformat(),
        "settings": record_current_settings(),
        "note": (
            "If these settings change, golden responses must be regenerated. "
            "Run: python tests/fixtures/generate_golden_responses.py"
        ),
    }

    save_golden_response("settings_snapshot.json", golden_response)


def generate_embedding_response() -> None:
    """Generate golden response for OpenAI embeddings."""
    print("\nGenerating embedding response...")

    embeddings_client = get_embeddings_client()

    # Generate embedding for test query
    embedding_vector = embeddings_client.client.embed_query(TEST_QUERY)

    golden_response = {
        "description": "OpenAI text-embedding-ada-002 response for test query",
        "generated_at": datetime.now().isoformat(),
        "settings": {
            "model": settings.embeddings_model,
            "query": TEST_QUERY,
        },
        "embedding": embedding_vector,
        "embedding_dimensions": len(embedding_vector),
        "note": "Real embedding from OpenAI API. Use for mocking in unit tests.",
    }

    save_golden_response("embedding_response.json", golden_response)
    print(f"Embedding dimensions: {len(embedding_vector)}")


def generate_chromadb_search_response() -> None:
    """Generate golden response for ChromaDB similarity search."""
    print("\nGenerating ChromaDB search response...")

    embeddings_client = get_embeddings_client()
    chroma_client = get_chroma_client()

    vdb_repo = get_vector_db_repository(
        chroma_client=chroma_client,
        embeddings_client=embeddings_client,
    )

    # Check if document exists
    if not vdb_repo.check_document_exists({"titulo": TEST_DOCUMENT_TITLE}):
        print(f"WARNING: Document '{TEST_DOCUMENT_TITLE}' not found in ChromaDB!")
        print("Please ingest ros-intro.pdf first:")
        print("POST /api/v1/document with ros-intro.pdf encoded in base64")
        return

    # Perform similarity search
    search_results = vdb_repo.similarity_search_with_score(
        query=TEST_QUERY,
        k=TEST_K_RESULTS,
        filter={"tipo-documento": {"$eq": TEST_DOCUMENT_TYPE}},
    )

    # Convert to serializable format
    results = [
        {
            "page_content": doc.page_content,
            "metadata": doc.metadata,
            "score": float(score),
        }
        for doc, score in search_results
    ]

    golden_response = {
        "description": "ChromaDB similarity search results for test query on ros-intro.pdf",
        "generated_at": datetime.now().isoformat(),
        "settings": {
            "collection": settings.chromadb_collection,
            "query": TEST_QUERY,
            "k_results": TEST_K_RESULTS,
            "filter": {"tipo-documento": TEST_DOCUMENT_TYPE},
            "document_title": TEST_DOCUMENT_TITLE,
        },
        "results": results,
        "result_count": len(results),
        "note": "Real ChromaDB search results. Use for mocking VectorDB in unit tests.",
    }

    save_golden_response("chromadb_search_response.json", golden_response)
    print(f"Retrieved {len(results)} chunks with scores: {[r['score'] for r in results]}")


def generate_llm_qa_response() -> None:
    """Generate golden response for LLM QA chain."""
    print("\nGenerating LLM QA response...")

    llm_client = get_llm_client()
    embeddings_client = get_embeddings_client()
    chroma_client = get_chroma_client()
    vdb_repo = get_vector_db_repository(
        chroma_client=chroma_client,
        embeddings_client=embeddings_client,
    )

    # Check if document exists
    if not vdb_repo.check_document_exists({"titulo": TEST_DOCUMENT_TITLE}):
        print(f"WARNING: Document '{TEST_DOCUMENT_TITLE}' not found in ChromaDB!")
        return

    # Get context from ChromaDB
    search_results = vdb_repo.similarity_search_with_score(
        query=TEST_QUERY,
        k=TEST_K_RESULTS,
        filter={"tipo-documento": {"$eq": TEST_DOCUMENT_TYPE}},
    )

    context = "\n\n".join([doc.page_content for doc, _ in search_results])

    # Create simple QA prompt
    prompt = f"""You are an assistant specialized in answering questions about documents.
Use the information provided in the context to answer the question.

Context:
{context}

Question:
{TEST_QUERY}

Answer:"""

    # Get LLM response
    response = llm_client.client.invoke(prompt)

    golden_response = {
        "description": "LLM QA response for test query on ros-intro.pdf",
        "generated_at": datetime.now().isoformat(),
        "settings": {
            "model": settings.openai_model,
            "temperature": settings.openai_temperature,
            "max_tokens": settings.openai_max_tokens,
            "top_p": settings.openai_top_p,
            "query": TEST_QUERY,
            "document_title": TEST_DOCUMENT_TITLE,
            "k_results": TEST_K_RESULTS,
        },
        "input": {
            "query": TEST_QUERY,
            "context_chunks": len(search_results),
        },
        "response": {
            "content": response.content,
            "model": getattr(response, "response_metadata", {}).get(
                "model_name", settings.openai_model
            ),
        },
        "source_documents": [
            {
                "page_content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score),
            }
            for doc, score in search_results
        ],
        "note": "Real LLM response. Use for mocking QA service in unit tests.",
    }

    save_golden_response("llm_qa_response.json", golden_response)
    print(f"LLM answer preview: {response.content[:100]}...")


def generate_cohere_rerank_response() -> None:
    """Generate golden response for Cohere reranking."""
    print("\nGenerating Cohere rerank response...")

    embeddings_client = get_embeddings_client()
    chroma_client = get_chroma_client()
    vdb_repo = get_vector_db_repository(
        chroma_client=chroma_client,
        embeddings_client=embeddings_client,
    )

    # Check if document exists
    if not vdb_repo.check_document_exists({"titulo": TEST_DOCUMENT_TITLE}):
        print(f"WARNING: Document '{TEST_DOCUMENT_TITLE}' not found in ChromaDB!")
        return

    # Get initial search results
    search_results = vdb_repo.similarity_search_with_score(
        query=TEST_QUERY,
        k=TEST_K_RESULTS,
        filter={"tipo-documento": {"$eq": TEST_DOCUMENT_TYPE}},
    )

    documents = [doc for doc, _ in search_results]

    # Perform reranking
    reranker = CohereRerank(
        top_n=TEST_RERANK_TOP_N,
        model=settings.cohere_model,
        cohere_api_key=settings.cohere_api_key,
    )

    reranked_docs = reranker.compress_documents(documents=documents, query=TEST_QUERY)

    golden_response = {
        "description": "Cohere rerank-v3.5 reranking results for test query",
        "generated_at": datetime.now().isoformat(),
        "settings": {
            "model": settings.cohere_model,
            "query": TEST_QUERY,
            "initial_k_results": TEST_K_RESULTS,
            "rerank_top_n": TEST_RERANK_TOP_N,
            "document_title": TEST_DOCUMENT_TITLE,
        },
        "input": {
            "query": TEST_QUERY,
            "documents_count": len(documents),
            "top_n": TEST_RERANK_TOP_N,
        },
        "reranked_documents": [
            {
                "page_content": doc.page_content,
                "metadata": doc.metadata,
            }
            for doc in reranked_docs
        ],
        "reranked_count": len(reranked_docs),
        "note": "Real Cohere reranking results. Use for mocking rerank service in unit tests.",
    }

    save_golden_response("cohere_rerank_response.json", golden_response)
    print(f"Reranked {len(documents)} -> {len(reranked_docs)} documents")


def generate_rerank_qa_complete_response() -> None:
    """Generate golden response for complete rerank QA (reranking + LLM answer)."""
    print("\nGenerating complete rerank QA response...")

    llm_client = get_llm_client()
    embeddings_client = get_embeddings_client()
    chroma_client = get_chroma_client()
    vdb_repo = get_vector_db_repository(
        chroma_client=chroma_client,
        embeddings_client=embeddings_client,
    )

    # Check if document exists
    if not vdb_repo.check_document_exists({"titulo": TEST_DOCUMENT_TITLE}):
        print(f"WARNING: Document '{TEST_DOCUMENT_TITLE}' not found in ChromaDB!")
        return

    # Get initial search results
    search_results = vdb_repo.similarity_search_with_score(
        query=TEST_QUERY,
        k=TEST_K_RESULTS,
        filter={"tipo-documento": {"$eq": TEST_DOCUMENT_TYPE}},
    )

    documents = [doc for doc, _ in search_results]

    # Perform reranking
    reranker = CohereRerank(
        top_n=TEST_RERANK_TOP_N,
        model=settings.cohere_model,
        cohere_api_key=settings.cohere_api_key,
    )

    reranked_docs = reranker.compress_documents(documents=documents, query=TEST_QUERY)

    # Build context from reranked documents
    context = "\n\n".join([doc.page_content for doc in reranked_docs])

    # Create QA prompt with reranked context
    prompt = f"""You are an assistant specialized in answering questions about documents.
Use the information provided in the context to answer the question.

Context:
{context}

Question:
{TEST_QUERY}

Answer:"""

    # Get LLM response
    response = llm_client.client.invoke(prompt)

    golden_response = {
        "description": "Complete rerank QA response (reranking + LLM answer) for test query",
        "generated_at": datetime.now().isoformat(),
        "settings": {
            "model": settings.openai_model,
            "temperature": settings.openai_temperature,
            "max_tokens": settings.openai_max_tokens,
            "top_p": settings.openai_top_p,
            "cohere_model": settings.cohere_model,
            "query": TEST_QUERY,
            "document_title": TEST_DOCUMENT_TITLE,
            "initial_k_results": TEST_K_RESULTS,
            "rerank_top_n": TEST_RERANK_TOP_N,
        },
        "input": {
            "query": TEST_QUERY,
            "initial_documents_count": len(documents),
            "reranked_documents_count": len(reranked_docs),
        },
        "reranked_documents": [
            {
                "page_content": doc.page_content,
                "metadata": doc.metadata,
            }
            for doc in reranked_docs
        ],
        "response": {
            "content": response.content,
            "model": getattr(response, "response_metadata", {}).get(
                "model_name", settings.openai_model
            ),
        },
        "note": "Complete rerank QA with final LLM answer. Use for testing RerankService.",
    }

    save_golden_response("rerank_qa_complete_response.json", golden_response)
    print(
        f"Complete rerank QA: {len(documents)} -> {len(reranked_docs)} docs, "
        f"answer preview: {response.content[:80]}..."
    )


def generate_sample_pdf_base64() -> None:
    """Generate base64-encoded sample PDF for testing."""
    print("\nGenerating sample PDF base64...")

    pdf_path = DOCUMENTS_DIR / "ros-intro.pdf"

    if not pdf_path.exists():
        print(f"WARNING: {pdf_path} not found!")
        return

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    base64_content = base64.b64encode(pdf_bytes).decode("utf-8")

    golden_response = {
        "description": "Base64-encoded ros-intro.pdf for testing PDF ingestion",
        "generated_at": datetime.now().isoformat(),
        "file_info": {
            "filename": "ros-intro.pdf",
            "size_bytes": len(pdf_bytes),
            "base64_length": len(base64_content),
        },
        "base64_content": base64_content,
        "base64_preview": base64_content[:100] + "...",
        "note": "Full base64 PDF content. Use for testing DocumentIngestionService.",
    }

    save_golden_response("sample_pdf_base64.json", golden_response)
    print(f"PDF size: {len(pdf_bytes)} bytes -> {len(base64_content)} base64 chars")


def main():
    print("=" * 80)
    print("Golden Response Generator for RAG-docs Unit Tests")
    print("=" * 80)
    print("\nTest Configuration:")
    print(f"  Document: {TEST_DOCUMENT_TITLE}")
    print(f"  Query: {TEST_QUERY}")
    print(f"  K Results: {TEST_K_RESULTS}")
    print(f"  Rerank Top N: {TEST_RERANK_TOP_N}")

    # Create golden responses directory if not exists
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Generate all golden responses
        generate_settings_snapshot()
        generate_embedding_response()
        generate_chromadb_search_response()
        generate_llm_qa_response()
        generate_cohere_rerank_response()
        generate_rerank_qa_complete_response()
        generate_sample_pdf_base64()

        print("\n" + "=" * 80)
        print("All golden responses generated successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\nError generating golden responses: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure ChromaDB is running")
        print("  2. Ensure ros-intro.pdf is ingested in ChromaDB")
        print("  3. Check API keys in .env: OPENAI_API_KEY, COHERE_API_KEY")
        raise


if __name__ == "__main__":
    main()
