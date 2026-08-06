"""Document domain model representing an entire document."""

from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

from app.knowledge.models.page import Page


class Document(BaseModel):
    """Represents a full document object containing extracted page objects.

    Attributes:
        id (str): Unique document identifier.
        filename (str): Original filename of the document.
        title (Optional[str]): Human-readable title or topic of the document.
        file_type (str): Format extension of the document (e.g. 'pdf').
        total_pages (int): Total number of pages in the document.
        pages (List[Page]): List of Page objects belonging to the document.
        metadata (Dict[str, Any]): Additional document-level metadata (e.g. author, creation date).
    """

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique UUID identifier for the document")
    filename: str = Field(..., description="Original filename of the document")
    title: Optional[str] = Field(default=None, description="Title of the document")
    file_type: str = Field(default="pdf", description="Document file extension or format type")
    total_pages: int = Field(default=0, description="Total page count")
    pages: List[Page] = Field(default_factory=list, description="Ordered list of page objects")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document-level metadata dictionary")

    @property
    def total_characters(self) -> int:
        """Returns aggregate character count across all pages."""
        return sum(page.char_count for page in self.pages)
