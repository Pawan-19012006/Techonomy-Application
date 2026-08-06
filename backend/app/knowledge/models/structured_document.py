"""StructuredDocument and DocumentStatistics domain models."""

from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

from app.knowledge.models.section import Section


class DocumentStatistics(BaseModel):
    """Calculated structural and quantitative statistics for a document.

    Attributes:
        total_pages (int): Total page count.
        total_headings (int): Count of detected heading elements.
        total_sections (int): Total section count.
        total_paragraphs (int): Count of detected paragraph elements.
        total_lists (int): Count of detected bullet or numbered list blocks.
        total_tables (int): Count of detected table structures.
        total_characters (int): Total aggregate character count.
        average_section_length (float): Average character length per section.
    """

    total_pages: int = Field(default=0, description="Total page count")
    total_headings: int = Field(default=0, description="Count of heading elements")
    total_sections: int = Field(default=0, description="Total section count")
    total_paragraphs: int = Field(default=0, description="Count of paragraph elements")
    total_lists: int = Field(default=0, description="Count of list blocks")
    total_tables: int = Field(default=0, description="Count of table elements")
    total_characters: int = Field(default=0, description="Total character count across all sections")
    average_section_length: float = Field(default=0.0, description="Average character length per section")


class StructuredDocument(BaseModel):
    """Represents a fully structured document containing typed sections, hierarchy, and statistics.

    Attributes:
        id (str): Unique UUID identifier for the structured document.
        filename (str): Original filename.
        title (Optional[str]): Human-readable document title.
        file_type (str): Format extension (e.g. 'pdf').
        sections (List[Section]): Flat ordered list of all extracted sections in reading order.
        hierarchy (List[Section]): Top-level root sections containing nested child structures.
        statistics (DocumentStatistics): Aggregate document metrics and element counts.
        metadata (Dict[str, Any]): Enriched document-level metadata.
    """

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique UUID identifier")
    filename: str = Field(..., description="Original filename")
    title: Optional[str] = Field(default=None, description="Document title")
    file_type: str = Field(default="pdf", description="Document file extension")
    sections: List[Section] = Field(default_factory=list, description="Flat ordered list of all sections")
    hierarchy: List[Section] = Field(default_factory=list, description="Top-level root section hierarchy tree")
    statistics: DocumentStatistics = Field(default_factory=DocumentStatistics, description="Document statistics")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document-level metadata dictionary")
