# Golden Responses Directory

This directory contains pre-recorded responses from external services for deterministic unit testing.

## Purpose

Instead of calling real APIs during unit tests, we:
1. **Record** real API responses once (manually or via script)
2. **Store** them as JSON files (golden responses)
3. **Replay** them in unit tests for fast, deterministic, offline testing

## Files

- `embedding_response.json` - OpenAI text-embedding-ada-002 response
- `chromadb_search_response.json` - ChromaDB similarity search results
- `cohere_rerank_response.json` - Cohere reranking results

## Generating Golden Responses

Run the generator script to create/update golden responses:

```bash
python tests/fixtures/generate_golden_responses.py
```

**Prerequisites:**
- ChromaDB must be running
- `.env` file must have valid API keys (OPENAI_API_KEY, COHERE_API_KEY)
- At least one document must be ingested in ChromaDB

## When to Regenerate

Regenerate golden responses when:
- External service APIs change
- You want to test with different data
- Golden response files are missing

## Structure

Each golden response file should contain:
```json
{
  "description": "What this response represents",
  "recorded_at": "ISO timestamp",
  "input": { "parameters used to generate this response" },
  "output": { "the actual response data" }
}
```
