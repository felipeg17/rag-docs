# RAG - DOCS

## Requirements


## Installation


### Running

- ChromaDB:

```bash
docker start chromadb
```

- Backend (FastAPI) + Frontend (Python Streamlit):

```bash
# Detached mode
docker compose up -d --build 

# Attached mode - logs shown in terminal
docker compose up --build
```

- Stopping the services:

```bash
docker compose down
```