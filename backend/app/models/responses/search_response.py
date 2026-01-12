from typing import List

from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    content: str = Field(..., description="Text content of the chunk")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    metadata: dict = Field(..., description="Chunk metadata (page, source, etc.)")


class DocumentSearchResponse(BaseModel):
    query: str = Field(..., description="Original search query")
    results: List[SearchResultItem] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results returned")
