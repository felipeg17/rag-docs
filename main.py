from fastapi import FastAPI

from app.routers.health import router as health_router
from app.routers.api import router as api_router

app = FastAPI(
  title="docs-rag-ms",
  version="0.0.1",
)

app.include_router(health_router)
app.include_router(api_router)