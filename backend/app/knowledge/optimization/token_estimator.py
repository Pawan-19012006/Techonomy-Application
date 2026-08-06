"""Token Estimator using fast character heuristic without external tokenizer dependencies."""

from typing import List
from app.knowledge.exceptions import TokenEstimatorError
from app.knowledge.models.knowledge_chunk import KnowledgeChunk
from app.utils.logging import logger


class TokenEstimator:
    """Estimates token counts for text and KnowledgeChunk objects using a character-ratio heuristic."""

    # Default heuristic: ~4 characters per token for English text
    DEFAULT_CHARS_PER_TOKEN = 4.0

    @classmethod
    def estimate_tokens(cls, text: str, chars_per_token: float = DEFAULT_CHARS_PER_TOKEN) -> int:
        """Estimates token count for a given text string.

        Args:
            text (str): Input text string.
            chars_per_token (float): Character-to-token ratio (default 4.0).

        Returns:
            int: Estimated token count (minimum 0 if text is empty, 1 if non-empty).
        """
        if not text or not text.strip():
            return 0
        ratio = chars_per_token if chars_per_token > 0 else cls.DEFAULT_CHARS_PER_TOKEN
        tokens = int(round(len(text) / ratio))
        return max(1, tokens)

    @classmethod
    def enrich_chunk(cls, chunk: KnowledgeChunk, chars_per_token: float = DEFAULT_CHARS_PER_TOKEN) -> KnowledgeChunk:
        """Calculates and sets estimated token count on a KnowledgeChunk object.

        Args:
            chunk (KnowledgeChunk): Target chunk.
            chars_per_token (float): Character-to-token ratio.

        Returns:
            KnowledgeChunk: Updated KnowledgeChunk object.
        """
        tokens = cls.estimate_tokens(chunk.content, chars_per_token=chars_per_token)
        chunk.estimated_tokens = tokens
        chunk.metadata["estimated_tokens"] = tokens
        chunk.metadata["character_count"] = len(chunk.content)
        return chunk

    @classmethod
    def enrich_chunks(cls, chunks: List[KnowledgeChunk], chars_per_token: float = DEFAULT_CHARS_PER_TOKEN) -> List[KnowledgeChunk]:
        """Calculates and sets estimated token counts across a list of KnowledgeChunk objects.

        Args:
            chunks (List[KnowledgeChunk]): List of KnowledgeChunk objects.
            chars_per_token (float): Character-to-token ratio.

        Returns:
            List[KnowledgeChunk]: List of enriched KnowledgeChunk objects.

        Raises:
            TokenEstimatorError: If token calculation fails.
        """
        try:
            for chunk in chunks:
                cls.enrich_chunk(chunk, chars_per_token=chars_per_token)
            logger.debug(f"Calculated token estimates for {len(chunks)} chunks.")
            return chunks
        except Exception as e:
            logger.error(f"Token estimation failed: {e}")
            raise TokenEstimatorError(f"Failed to calculate token estimates: {str(e)}") from e
