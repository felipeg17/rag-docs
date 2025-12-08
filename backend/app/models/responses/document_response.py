from typing import Literal

from pydantic import BaseModel, Field


class DocumentIngestResponse(BaseModel):
    # TODO: Analyze if using an uuid is a good strategy
    document_id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title")
    status: Literal["created", "updated"] = Field(..., description="Creation status")
    # Just a human readable comment to clarify the status
    message: str = Field(..., description="Status message")
