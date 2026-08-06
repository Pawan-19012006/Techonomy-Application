"""KnowledgeChunk domain model representing an optimized semantic text chunk for vector embedding."""

from typing import Any, Dict, List
from uuid import uuid4
from pydantic import BaseModel, Field


class KnowledgeChunk(BaseModel):
    """Represents a high-quality semantic text chunk prepared for vector embedding and retrieval.

    Attributes:
        chunk_id (str): Unique UUID identifier for the chunk.
        document_id (str): UUID reference to parent Document.
        page_numbers (List[int]): List of 1-indexed page numbers covered by this chunk.
        section_title (str): Title of the primary section or heading governing this chunk.
        section_type (str): Type classification (heading, paragraph, list, table, composite).
        hierarchy_level (int): Hierarchy depth level of governing section (1 = Top H1).
        reading_order (int): Sequential reading order index across the document (0-indexed).
        content (str): Text content body of the chunk.
        estimated_tokens (int): Approximate token count calculated by TokenEstimator.
        metadata (Dict[str, Any]): Enriched metadata dictionary.
    """

    chunk_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique UUID identifier for chunk")
    document_id: str = Field(..., description="Parent document UUID reference")
    page_numbers: List[int] = Field(default_factory=list, description="List of 1-indexed page numbers covered")
    section_title: str = Field(..., description="Title of the governing section")
    section_type: str = Field(default="composite", description="Structural type: heading, paragraph, list, table, composite")
    hierarchy_level: int = Field(default=1, description="Hierarchy level depth")
    reading_order: int = Field(..., description="Sequential reading order index across document")
    content: str = Field(..., description="Text content body of chunk")
    estimated_tokens: int = Field(default=0, description="Estimated token count")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata dictionary")

    @property
    def char_count(self) -> int:
        """Returns total character count of chunk content."""
        return len(self.content)
