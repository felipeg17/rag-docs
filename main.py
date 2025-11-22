from fastapi import FastAPI

from app.core.lifespan import lifespan
from app.routers.api import router as api_router
from app.routers.health import router as health_router


app = FastAPI(title="docs-rag-ms", version="0.0.1", lifespan=lifespan)

app.include_router(health_router)
app.include_router(api_router)
