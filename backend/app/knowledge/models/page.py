"""Page domain model representing a single document page."""

from typing import Any, Dict
from pydantic import BaseModel, Field


class Page(BaseModel):
    """Represents a single extracted page from a document.

    Attributes:
        page_number (int): 1-indexed page number within the document.
        text (str): Raw or cleaned text content of the page.
        metadata (Dict[str, Any]): Additional page-level metadata (e.g. char count, dimensions).
    """

    page_number: int = Field(..., description="1-indexed page number within the document")
    text: str = Field(..., description="Text content extracted from the page")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Page-level metadata dictionary")

    @property
    def char_count(self) -> int:
        """Returns total character count of the page text."""
        return len(self.text)
