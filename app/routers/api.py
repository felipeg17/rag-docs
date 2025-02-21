from fastapi import APIRouter
from app.procesar_documento.controller.process_document_controller import \
  router as process_variables_router

router = APIRouter(
  prefix="/rag-docs",
  tags=["Procesar documentos"]
)

router.include_router(process_variables_router)
