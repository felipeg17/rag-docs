from fastapi import FastAPI

from app.api.routers.api import router as api_router
from app.api.routers.health import router as health_router
from app.core.lifespan import lifespan


app = FastAPI(title="docs-rag-ms", version="0.0.1", lifespan=lifespan)

app.include_router(health_router)
app.include_router(api_router)
