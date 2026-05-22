# Frontend

Streamlit-based web UI for document upload and conversational Q&A.

## Overview

The frontend provides a user-friendly interface for:
- **PDF Upload**: Ingest documents into the backend
- **Chatbot**: Ask questions about uploaded documents

Built with Streamlit for rapid development and ease of deployment.

## Quick Start

### Docker

```bash
cd ..
docker compose --env-file image.env --profile full up --build
```

Frontend runs at `http://localhost:8501`.

### Local Development

```bash
python -m venv .venv
source .venv/bin/activate
uv pip install -e .
cp frontend.env.template frontend.env

# Edit frontend.env and set API_HOST=localhost and API_PORT=8106

# Start server
streamlit run front.py
```

Frontend runs at `http://localhost:8501`.

## Features

### Document Upload Page

- Upload PDF files
- See ingestion progress and chunk count
- Display document metadata (title, upload date)

### Chatbot Page

- Select a document from uploaded files
- Enter questions in natural language
- Choose retrieval strategy:
  - **Standard RAG**: Fast, uses all retrieved chunks
  - **Reranking**: More expensive but potentially more accurate (requires Cohere API key)

## Project Structure

```
frontend/
├── components/
│   ├── chatbot.py          # Chat interface component
│   └── qa_pdf.py           # PDF Q&A component
├── pages/                  # Streamlit multi-page stubs
├── src/                    # Shared utilities
├── utils/                  # Helper functions
├── front.py                # App entry point
├── pyproject.toml          # Dependencies
└── frontend.env.template   # Configuration template
```

## Testing

Backend integration tests cover the full flow. For frontend-specific testing:

```bash
# Manual testing in Streamlit
streamlit run front.py
```
