"""Query Processor for normalizing, validating, and preparing user search questions."""

import re
from typing import Any, Dict
from app.knowledge.exceptions import QueryProcessorError
from app.knowledge.models.processed_query import ProcessedQuery
from app.utils.logging import logger


class QueryProcessor:
    """Normalizes and validates raw user questions for vector search."""

    def __init__(self, max_length: int = 2048):
        """Initializes QueryProcessor with length constraints.

        Args:
            max_length (int): Maximum allowed character length for input query.
        """
        self.max_length = max_length

    def process(self, raw_query: str) -> ProcessedQuery:
        """Processes, validates, and normalizes a raw user query string.

        Args:
            raw_query (str): Raw input question string.

        Returns:
            ProcessedQuery: Validated and normalized ProcessedQuery domain model.

        Raises:
            QueryProcessorError: If query is empty, whitespace-only, or exceeds max_length.
        """
        if not raw_query or not raw_query.strip():
            logger.error("QueryProcessor received an empty or whitespace-only query.")
            raise QueryProcessorError("User query cannot be empty or blank.")

        trimmed = raw_query.strip()
        if len(trimmed) > self.max_length:
            logger.error(f"Query length ({len(trimmed)}) exceeds max_length ({self.max_length}).")
            raise QueryProcessorError(f"Query length ({len(trimmed)}) exceeds maximum allowed ({self.max_length}).")

        # Normalize whitespace (collapse multiple spaces into single space)
        normalized = re.sub(r"\s+", " ", trimmed)

        words = normalized.split()
        char_count = len(normalized)
        word_count = len(words)

        logger.info(
            f"Processed user query: original='{raw_query[:50]}...', "
            f"normalized='{normalized[:50]}...' [Chars: {char_count}, Words: {word_count}]"
        )

        return ProcessedQuery(
            original_query=raw_query,
            normalized_query=normalized,
            character_count=char_count,
            word_count=word_count,
            is_valid=True,
            metadata={"processed_by": "QueryProcessor", "version": "1.0"},
        )
