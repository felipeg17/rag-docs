import base64
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class DocumentIngestRequest(BaseModel):
    title: str = Field(..., description="Document title, must be unique")
    document_type: Optional[str] = Field(
        default="documento-pdf", description="Document type (pdf, csv, etc)"
    )
    # The actual text encoded in base64
    document_content: str = Field(..., description="Base64-encoded document content")

    @field_validator("document_content")
    @classmethod
    def validate_base64(cls, content: str) -> str:
        try:
            base64.b64decode(content, validate=True)
            return content
        except Exception:
            raise ValueError("Invalid base64 encoding")
