from typing import Optional

from pydantic import BaseModel, Field


class ProcessDocumentRequest(BaseModel):
    title: str
    document_type: Optional[str] = Field(
        default="documento-pdf",
    )
    # The actual text encoded in base64
    document_content: str


class SearchVectorDataBaseRequest(BaseModel):
    title: Optional[str] = Field(
        default=None,
    )
    document_type: Optional[str] = Field(
        default="documento-pdf",
    )
    query: str
    k_results: Optional[int] = Field(
        default=4,
    )
    metadata_filter: Optional[dict] = Field(
        default={},
    )
