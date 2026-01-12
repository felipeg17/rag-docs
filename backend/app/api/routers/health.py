from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_db_client
from app.infrastructure.database.client import DatabaseClient


router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check(db_client: Annotated[DatabaseClient, Depends(get_db_client)]):
    db_status = "connected" if db_client.heartbeat() else "disconnected"
    return {
        "status": "healthy",
        "database": db_status,
    }
