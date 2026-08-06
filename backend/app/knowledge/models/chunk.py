"""Chunk domain model definition."""

from typing import Any, Dict, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """Represents a text chunk derived from a document.

    Note:
        This model definition prepares the system for future chunking stages.
        No chunking logic is performed in Phase 1.

    Attributes:
        id (str): Unique chunk identifier.
        document_id (str): Reference ID to parent Document.
        page_number (int): 1-indexed page number from which chunk originated.
        content (str): Chunk text content.
        chunk_index (int): Sequential index of chunk within the document.
        metadata (Dict[str, Any]): Additional metadata for vector indexing.
    """

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique UUID identifier for the chunk")
    document_id: str = Field(..., description="Parent document UUID reference")
    page_number: int = Field(..., description="1-indexed page number origin")
    content: str = Field(..., description="Chunk text content")
    chunk_index: int = Field(default=0, description="Sequential index of chunk in document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata dictionary")
