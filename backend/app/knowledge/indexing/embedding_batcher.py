"""Embedding Batcher for grouping KnowledgeChunk objects into batches."""

from typing import List
from app.config import settings
from app.knowledge.exceptions import EmbeddingBatcherError
from app.knowledge.models.knowledge_chunk import KnowledgeChunk
from app.utils.logging import logger


class EmbeddingBatcher:
    """Groups KnowledgeChunk lists into batches for efficient inference and upload."""

    @classmethod
    def create_batches(
        cls,
        chunks: List[KnowledgeChunk],
        batch_size: int = settings.EMBEDDING_BATCH_SIZE,
    ) -> List[List[KnowledgeChunk]]:
        """Groups chunks into batches of size batch_size.

        Args:
            chunks (List[KnowledgeChunk]): List of KnowledgeChunk objects.
            batch_size (int): Max number of chunks per batch (default 32).

        Returns:
            List[List[KnowledgeChunk]]: List of batched KnowledgeChunk lists.

        Raises:
            EmbeddingBatcherError: If batch_size <= 0 or batching fails.
        """
        if batch_size <= 0:
            logger.error(f"Invalid batch_size={batch_size}. Batch size must be > 0.")
            raise EmbeddingBatcherError(f"Batch size must be > 0, got {batch_size}")

        if not chunks:
            return []

        logger.debug(f"Grouping {len(chunks)} chunks into batches of size {batch_size}...")

        try:
            batches: List[List[KnowledgeChunk]] = []
            for i in range(0, len(chunks), batch_size):
                batches.append(chunks[i : i + batch_size])

            logger.info(f"Created {len(batches)} batches from {len(chunks)} chunks.")
            return batches

        except Exception as e:
            logger.error(f"Embedding batching failed: {e}")
            raise EmbeddingBatcherError(f"Failed to batch chunks: {str(e)}") from e
