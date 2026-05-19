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

# Edit frontend.env with backend URL (default: http://localhost:8106)

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
- View AI-generated answers with source document snippets
- Choose retrieval strategy:
  - **Standard RAG**: Fast, uses all retrieved chunks
  - **Reranking**: More expensive but potentially more accurate (requires Cohere API key)

## Project Structure

```
frontend/
├── components/             # Reusable UI components
│   ├── document_upload.py
│   ├── chat_interface.py
│   └── ...
├── pages/                  # Streamlit pages (multi-page app)
│   ├── upload.py           # Document ingestion page
│   └── chat.py             # Q&A chatbot page
├── src/                    # Shared utilities
│   └── api_client.py       # Backend API interaction
├── utils/                  # Helper functions
│   ├── formatting.py
│   └── ...
├── front.py                # App entry point
├── pyproject.toml          # Dependencies
└── frontend.env.template   # Configuration template
```

## Configuration

Copy `frontend.env.template` to `frontend.env`:

```bash
BACKEND_URL=http://localhost:8106
```

If running in Docker or remote, point to the correct backend URL.

## Development

### Running Locally

```bash
cd frontend
source .venv/bin/activate
streamlit run front.py
```

Streamlit automatically reloads on code changes.

### File Organization

- `front.py`: App configuration and navigation
- `pages/`: Multi-page app pages (auto-loaded by Streamlit)
- `components/`: Reusable Streamlit components
- `src/`: Non-UI business logic and API clients
- `utils/`: Helper functions

### Adding a New Page

Create a file in `pages/` (e.g., `pages/analytics.py`):

```python
import streamlit as st
from src.api_client import get_insights

st.title("Analytics")

# Page content here
insights = get_insights()
st.write(insights)
```

Streamlit auto-discovers and adds to navigation.

### Adding a New Component

Create a file in `components/` (e.g., `components/document_filter.py`):

```python
import streamlit as st

def document_filter():
    selected = st.selectbox("Choose document", ["doc1", "doc2"])
    return selected
```

Use in pages:

```python
from components.document_filter import document_filter

selected_doc = document_filter()
```

## API Integration

Interact with the backend via `src/api_client.py`:

```python
from src.api_client import ingest_document, ask_question

# Upload document
result = ingest_document(file=pdf_bytes, titulo="my-doc")

# Ask question
answer = ask_question(document_id="my-doc", question="What is RAG?")
```

## Testing

Backend integration tests cover the full flow. For frontend-specific testing:

```bash
# Manual testing in Streamlit
streamlit run front.py

# Test specific page
streamlit run pages/chat.py
```

No automated frontend tests currently. Contributions welcome.

## Troubleshooting

### Backend Connection Error

Ensure backend is running and `BACKEND_URL` in `frontend.env` is correct:

```bash
curl http://localhost:8106/health
```

### Port 8501 Already in Use

Change Streamlit port:

```bash
streamlit run front.py --server.port 8502
```

### Slow Upload

Large PDFs may take time to upload and process. Check backend logs:

```bash
docker compose logs backend
```

### Cached Data Issues

Clear Streamlit cache:

```bash
streamlit cache clear
```

## Deployment

### Docker

See root-level Docker Compose in `../docker-compose.yml`.

### Manual Deployment

```bash
# Install dependencies
uv pip install -e .

# Run with Streamlit server
streamlit run front.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --logger.level=info
```

## Contributing

See `../docs/CONTRIBUTING.md` for guidelines.

## Resources

- [Streamlit Docs](https://docs.streamlit.io/)
- [Setup Guide](../docs/SETUP.md)
- [Backend README](../backend/README.md)
- [Main README](../README.md)
