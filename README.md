# RAG - DOCS

## Requirements

## Installation

### Running

- ChromaDB:

```bash
docker start chromadb
```

- Backend (FastAPI) + Frontend (Python Streamlit):

Using `full` profile.

```bash
# Detached mode
docker compose --profile full up -d --build

# Attached mode - logs shown in terminal
docker compose --profile full up --build
```

- Stopping the services:

```bash
docker compose down
```
