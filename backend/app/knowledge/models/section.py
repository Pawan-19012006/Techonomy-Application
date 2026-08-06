"""Section domain model representing a structured component of a document."""

from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class Section(BaseModel):
    """Represents a structural element (heading, section, paragraph, list, table) of a document.

    Attributes:
        id (str): Unique UUID identifier for the section.
        title (str): Title or headline of the section.
        section_type (str): Type classification ('heading', 'section', 'subsection', 'paragraph', 'list', 'table').
        level (int): Hierarchy depth level (1 = H1/Main Section, 2 = H2/Subsection, 3 = H3, 4 = Paragraph/List/Table).
        content (str): Text content of the structural element.
        page_number (int): 1-indexed page number where the section originates.
        reading_order (int): Sequential reading order index across the full document (0-indexed).
        parent_id (Optional[str]): UUID of the parent Section in the document hierarchy tree.
        children_ids (List[str]): List of child Section UUIDs belonging to this section.
        metadata (Dict[str, Any]): Enriched metadata dictionary.
    """

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique UUID identifier for the section")
    title: str = Field(default="", description="Headline or title of the section")
    section_type: str = Field(default="paragraph", description="Type classification: heading, section, subsection, paragraph, list, table")
    level: int = Field(default=1, description="Hierarchy depth level (1 = Top H1, 2 = H2, etc.)")
    content: str = Field(..., description="Text body of the structural section")
    page_number: int = Field(..., description="1-indexed origin page number")
    reading_order: int = Field(..., description="Sequential reading order index across the document")
    parent_id: Optional[str] = Field(default=None, description="UUID of parent section in hierarchy")
    children_ids: List[str] = Field(default_factory=list, description="IDs of direct child sections")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Section metadata dictionary")

    @property
    def char_count(self) -> int:
        """Returns character count of section content."""
        return len(self.content)
