from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class SourceDocument(BaseModel):
    page_content: str = Field(..., description="Content of the source chunk")
    metadata: dict = Field(..., description="Metadata (page number, etc.)")
    score: Optional[float] = Field(None, description="Relevance score (if available)")


class QuestionAnswerResponse(BaseModel):
    question: str = Field(..., description="Original question")
    answer: Optional[str] = Field(
        ..., description="Generated answer (error 404 if document not found)"
    )
    document_id: str = Field(..., description="Document that was queried")
    strategy: Literal["standard", "rerank"] = Field(..., description="Strategy used")
    source_documents: List[SourceDocument] = Field(
        default_factory=list, description="Source documents used for the answer"
    )
