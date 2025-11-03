from fastapi import APIRouter


router = APIRouter(prefix="/rag-docs", tags=["Health"])


@router.get("/health", status_code=200, tags=["Health"])
def health_msg():
    return {"status": "service up"}
