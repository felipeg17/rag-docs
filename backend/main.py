from fastapi import APIRouter, FastAPI

from app.api.routers.health import router as health_router
from app.api.routers.v1.document import router as documents_router
from app.core.lifespan import lifespan


app = FastAPI(title="docs-rag-ms", version="0.0.2", lifespan=lifespan)

# Health
app.include_router(health_router)

# API v1
api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(documents_router)
app.include_router(api_v1)
