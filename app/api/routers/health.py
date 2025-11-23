from fastapi import APIRouter, status


router = APIRouter(prefix="/rag-docs", tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
def health_msg():
    return {"status": "service up"}
