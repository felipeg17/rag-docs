# rag-docs

## Requirements

## Installation

### Running

- ChromaDB:

```bash
docker start chromadb
```

- Backend (FastAPI) + Frontend (Python Streamlit):

Using `full` profile and the `image.env` file.

```bash
# Detached mode
docker compose --env-file image.env --profile full up -d --build

# Attached mode - logs shown in terminal
docker compose --env-file image.env --profile full up --build
```

- Stopping the services:

```bash
docker compose down
```

#### Skaffold

```
skaffold dev --profile local -f skaffold.yaml
```
