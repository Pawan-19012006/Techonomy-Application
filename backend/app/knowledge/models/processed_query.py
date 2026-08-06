"""ProcessedQuery domain model representing normalized user search queries."""

from typing import Any, Dict
from pydantic import BaseModel, Field


class ProcessedQuery(BaseModel):
    """Represents a validated and normalized user query.

    Attributes:
        original_query (str): Raw input query string from user.
        normalized_query (str): Cleaned and normalized query text.
        character_count (int): Character count of normalized query.
        word_count (int): Tokenized word count of query.
        is_valid (bool): Validation status flag.
        metadata (Dict[str, Any]): Additional query processing metadata.
    """

    original_query: str = Field(..., description="Raw input user query")
    normalized_query: str = Field(..., description="Normalized and cleaned query string")
    character_count: int = Field(..., description="Character length of normalized query")
    word_count: int = Field(..., description="Word count of normalized query")
    is_valid: bool = Field(default=True, description="Query validity flag")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary for query expansion")
