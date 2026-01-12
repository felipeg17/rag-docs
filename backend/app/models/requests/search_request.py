from typing import Literal

from pydantic import BaseModel, Field


class DocumentSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    k_results: int = Field(default=4, ge=1, le=10, description="Number of results")
    metadata_filter: dict = Field(default={}, description="Optional metadata filters")


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question to ask")
    strategy: Literal["standard", "rerank"] = Field(
        default="standard", description="QA strategy: 'standard' or 'rerank'"
    )
    k_results: int = Field(default=4, ge=1, le=10, description="Number of chunks to retrieve")
    metadata_filter: dict = Field(default={}, description="Optional metadata filters")
