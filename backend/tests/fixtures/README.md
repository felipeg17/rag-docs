# Golden Responses Directory

This directory contains pre-recorded responses from external services for deterministic unit testing.

## Purpose

Instead of calling real APIs during unit tests, we:
1. **Record** real API responses once using the generator script
2. **Store** them as JSON files (golden responses)
3. **Replay** them in unit tests for fast, deterministic, offline testing

## Files

- `settings_snapshot.json` - Current settings used to generate golden responses
- `embedding_response.json` - OpenAI text-embedding-ada-002 response
- `chromadb_search_response.json` - ChromaDB similarity search results
- `llm_qa_response.json` - OpenAI LLM QA response with context
- `cohere_rerank_response.json` - Cohere reranking results (documents only)
- `rerank_qa_complete_response.json` - Complete rerank QA (reranked docs + LLM answer)
- `sample_pdf_base64.json` - Base64-encoded ros-intro.pdf for testing

**Note:** ChromaDB search scores may vary slightly (third decimal) due to floating-point precision in cosine similarity calculations. Tests should use tolerance when comparing scores.

## Generating Golden Responses

**Prerequisites:**
- ChromaDB must be running
- `ros-intro.pdf` must be ingested in ChromaDB (use POST /api/v1/document)
- `.env` file must have valid API keys (OPENAI_API_KEY, COHERE_API_KEY)

**Run the generator:**

```bash
# From project root
python tests/fixtures/generate_golden_responses.py
```

The script will:
1. Connect to real ChromaDB with ingested documents
2. Query real OpenAI embeddings and LLM
3. Query real Cohere reranking
4. Save all responses with metadata

## When to Regenerate

Regenerate golden responses when:
- External service APIs change
- Settings change (model, temperature, chunk size, etc.)
- You want to test with different data
- Golden response files are missing or corrupted

**Important:** Golden responses are tied to current settings. If you change:
- `openai_model`
- `openai_temperature`
- `default_chunk_size`
- `default_chunk_overlap`
- `cohere_model`

You MUST regenerate golden responses to maintain test accuracy.

## Structure

Each golden response file contains:

```json
{
  "description": "What this response represents",
  "generated_at": "ISO timestamp",
  "settings": {
    "model": "gpt-4o-mini",
    "temperature": 0.05,
    ...
  },
  "input": {
    "query": "test query",
    ...
  },
  "response": {
    "actual response data"
  },
  "note": "Usage instructions"
}
```

## Testing Workflow

1. **Generate golden responses** (one time or when settings change):
   ```bash
   python tests/fixtures/generate_golden_responses.py
   ```

2. **Run unit tests** (uses golden responses, no API calls):
   ```bash
   python -m unittest discover -s tests/unit -v
   ```

3. **Verify settings** before each test run:
   - Tests should compare current settings with `settings_snapshot.json`
   - Warn if settings mismatch (golden responses may be stale)

## Golden Responses vs Integration Tests

- **Unit tests + golden responses**: Fast, offline, deterministic, isolated
- **Integration tests**: Slower, require real services, end-to-end validation

Both are valuable! Golden responses enable fast unit testing while maintaining confidence that tests reflect real service behavior.
