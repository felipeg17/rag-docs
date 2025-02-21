from pydantic import BaseModel, Field
from typing import Optional, Literal

class ProcessDocumentRequest(BaseModel):
  title: str = Field(
    default=None,
  )
  document_type: Optional[str] = Field(
    default="documento-pdf",
  )
  document_bytes: bytes = Field(
    default=None,
  )


class SearchVectorDataBaseRequest(BaseModel):
  title: Optional[str] = Field(
    default=None,
  )
  document_type: Optional[str] = Field(
    default="documento-pdf",
  )
  query: Optional[str] = Field(
    default=None,
  )
  k_results: Optional[int] = Field(
    default=4,
  )
  metadata_filter: Optional[dict] = Field(
    default={},
  )