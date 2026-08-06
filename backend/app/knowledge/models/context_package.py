"""ContextPackage domain model representing synthesized context ready for LLM consumption."""

from typing import Any, Dict, List
from pydantic import BaseModel, Field

from app.knowledge.models.search_result import SearchResult


class ContextPackage(BaseModel):
    """Represents a curated, merged, and budget-validated context package.

    Attributes:
        context_text (str): Synthesized context text ready for LLM prompt insertion.
        estimated_tokens (int): Total estimated token count of context_text.
        chunks_used (int): Number of source chunks merged into this context package.
        sources (List[str]): Formatted citation source strings (e.g. ['annual_report.pdf Page 42']).
        source_chunks (List[SearchResult]): List of SearchResult objects included in context.
        metadata (Dict[str, Any]): Additional context construction metadata.
    """

    context_text: str = Field(..., description="Synthesized context text ready for LLM prompt construction")
    estimated_tokens: int = Field(..., description="Total estimated token count of context text")
    chunks_used: int = Field(..., description="Number of chunks merged into context")
    sources: List[str] = Field(default_factory=list, description="Formatted citation strings (e.g. 'doc.pdf Page 5')")
    source_chunks: List[SearchResult] = Field(default_factory=list, description="List of source SearchResult objects")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Context construction metadata dictionary")
