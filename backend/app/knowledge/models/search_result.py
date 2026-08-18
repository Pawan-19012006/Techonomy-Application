"""SearchResult domain model representing a matched chunk from vector search."""

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Represents a single retrieved chunk match with similarity scoring and payload metadata.

    Attributes:
        chunk_id (str): Chunk UUID reference.
        document_id (str): Document UUID reference.
        document_name (str): Document filename or title.
        score (float): Similarity score (Cosine similarity or reranked score).
        content (str): Text content of the chunk.
        page_numbers (List[int]): Page numbers covered by the chunk.
        section_title (str): Section title header.
        section_type (str): Structural section type (heading, paragraph, list, table, composite).
        hierarchy_level (int): Structural hierarchy level depth (1-6).
        reading_order (int): Reading order index.
        estimated_tokens (int): Estimated token count.
        payload (Dict[str, Any]): Full raw Qdrant point payload dictionary.
    """

    chunk_id: str = Field(..., description="Chunk UUID reference")
    document_id: str = Field(..., description="Document UUID reference")
    document_name: str = Field(..., description="Document filename or title")
    document_type: str = Field(default="company", description="Document classification (company or instruction)")
    visibility: str = Field(default="user_visible", description="Document visibility (user_visible or internal)")
    score: float = Field(..., description="Cosine similarity or reranked score")
    content: str = Field(..., description="Text content body of chunk")
    page_numbers: List[int] = Field(default_factory=list, description="Page numbers list")
    section_title: str = Field(default="Untitled Section", description="Section title header")
    section_type: str = Field(default="composite", description="Structural section type")
    hierarchy_level: int = Field(default=2, description="Hierarchy level depth")
    reading_order: int = Field(default=0, description="Reading order sequence index")
    estimated_tokens: int = Field(default=0, description="Estimated token count")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Raw Qdrant point payload dictionary")
