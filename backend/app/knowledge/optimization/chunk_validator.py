"""Chunk Validator for auditing generated KnowledgeChunk objects prior to downstream indexing."""

from typing import List, Tuple
from app.knowledge.exceptions import ChunkValidatorError
from app.knowledge.models.chunk_statistics import ChunkStatistics
from app.knowledge.models.knowledge_chunk import KnowledgeChunk
from app.utils.logging import logger


class ChunkValidator:
    """Validates structural and constraint compliance across KnowledgeChunk objects."""

    DEFAULT_MAX_TOKENS = 512

    @classmethod
    def validate_chunks(
        cls,
        chunks: List[KnowledgeChunk],
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> Tuple[List[KnowledgeChunk], ChunkStatistics]:
        """Audits KnowledgeChunk objects and filters out invalid chunks.

        Validation Checks:
            - Content is non-empty.
            - Estimated tokens <= max_tokens.
            - Valid metadata dictionary populated.
            - Document ID present.
            - Page numbers list non-empty.
            - Section title present.

        Args:
            chunks (List[KnowledgeChunk]): List of KnowledgeChunk objects to validate.
            max_tokens (int): Maximum token budget ceiling.

        Returns:
            Tuple[List[KnowledgeChunk], ChunkStatistics]: Tuple of (valid_chunks, computed_chunk_statistics).

        Raises:
            ChunkValidatorError: If validation processing encounters unexpected error.
        """
        logger.info(f"Validating {len(chunks)} KnowledgeChunk objects against token limit {max_tokens}...")

        valid_chunks: List[KnowledgeChunk] = []
        rejected_count = 0

        try:
            for idx, chunk in enumerate(chunks):
                is_valid, reason = cls._validate_single(chunk, max_tokens=max_tokens)
                if is_valid:
                    valid_chunks.append(chunk)
                else:
                    rejected_count += 1
                    logger.warning(
                        f"Chunk #{chunk.reading_order} (ID: {chunk.chunk_id[:8]}) rejected: {reason}"
                    )

            stats = cls.calculate_statistics(valid_chunks)

            logger.info(
                f"Completed chunk validation. "
                f"Passed: {len(valid_chunks)}, Rejected: {rejected_count}, Total Tokens: {stats.total_tokens}."
            )
            return valid_chunks, stats

        except Exception as e:
            logger.error(f"Chunk validation failed: {e}")
            raise ChunkValidatorError(f"Failed to validate chunks: {str(e)}") from e

    @classmethod
    def _validate_single(cls, chunk: KnowledgeChunk, max_tokens: int) -> Tuple[bool, str]:
        """Validates a single KnowledgeChunk object against core constraints."""
        if not chunk.content or not chunk.content.strip():
            return False, "Chunk content is empty"

        if not chunk.document_id:
            return False, "Missing document_id"

        if not chunk.page_numbers:
            return False, "Missing page_numbers"

        if not chunk.section_title:
            return False, "Missing section_title"

        if not isinstance(chunk.metadata, dict) or not chunk.metadata:
            return False, "Missing or empty metadata dictionary"

        if chunk.estimated_tokens > max_tokens:
            return False, f"Estimated tokens ({chunk.estimated_tokens}) exceeds maximum limit ({max_tokens})"

        return True, "Valid"

    @classmethod
    def calculate_statistics(cls, chunks: List[KnowledgeChunk]) -> ChunkStatistics:
        """Computes ChunkStatistics across a list of valid KnowledgeChunk objects.

        Args:
            chunks (List[KnowledgeChunk]): List of valid KnowledgeChunk objects.

        Returns:
            ChunkStatistics: Quantitative metrics object.
        """
        if not chunks:
            return ChunkStatistics()

        total_chunks = len(chunks)
        total_chars = sum(c.char_count for c in chunks)
        total_tokens = sum(c.estimated_tokens for c in chunks)

        largest_chunk = max(c.char_count for c in chunks)
        smallest_chunk = min(c.char_count for c in chunks)

        avg_size = round(total_chars / total_chunks, 2)
        avg_tokens = round(total_tokens / total_chunks, 2)

        return ChunkStatistics(
            total_chunks=total_chunks,
            average_chunk_size=avg_size,
            largest_chunk=largest_chunk,
            smallest_chunk=smallest_chunk,
            average_tokens=avg_tokens,
            total_tokens=total_tokens,
        )
