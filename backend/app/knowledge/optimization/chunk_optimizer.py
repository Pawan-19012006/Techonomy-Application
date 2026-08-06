"""Chunk Optimizer for merging tiny chunks and splitting oversized chunks."""

from typing import List
from app.knowledge.exceptions import ChunkOptimizerError
from app.knowledge.models.knowledge_chunk import KnowledgeChunk
from app.knowledge.optimization.token_estimator import TokenEstimator
from app.utils.logging import logger


class ChunkOptimizer:
    """Optimizes generated KnowledgeChunk objects by merging small fragments and splitting oversized chunks."""

    DEFAULT_MIN_TOKENS = 30
    DEFAULT_MAX_TOKENS = 512

    @classmethod
    def optimize(
        cls,
        chunks: List[KnowledgeChunk],
        min_tokens: int = DEFAULT_MIN_TOKENS,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> List[KnowledgeChunk]:
        """Optimizes chunks by merging tiny chunks and splitting oversized chunks while maintaining reading order.

        Args:
            chunks (List[KnowledgeChunk]): Initial list of KnowledgeChunk objects.
            min_tokens (int): Minimum token threshold for merging tiny chunks.
            max_tokens (int): Maximum token threshold for splitting oversized chunks.

        Returns:
            List[KnowledgeChunk]: Optimized list of KnowledgeChunk objects.

        Raises:
            ChunkOptimizerError: If chunk optimization fails.
        """
        if not chunks:
            return []

        logger.info(f"Optimizing {len(chunks)} KnowledgeChunk objects (min_tokens={min_tokens}, max_tokens={max_tokens})...")

        try:
            # Step 1: Split any oversized chunks exceeding max_tokens
            split_chunks: List[KnowledgeChunk] = []
            for chunk in chunks:
                if chunk.estimated_tokens > max_tokens:
                    split_chunks.extend(cls._split_oversized_chunk(chunk, max_tokens=max_tokens))
                else:
                    split_chunks.append(chunk)

            # Step 2: Merge adjacent tiny chunks below min_tokens
            merged_chunks: List[KnowledgeChunk] = []
            i = 0
            while i < len(split_chunks):
                current = split_chunks[i]

                # If current chunk is below min_tokens and there is a next chunk
                if current.estimated_tokens < min_tokens and i + 1 < len(split_chunks):
                    next_chunk = split_chunks[i + 1]
                    combined_tokens = current.estimated_tokens + next_chunk.estimated_tokens

                    # Merge if combined size fits within max_tokens
                    if combined_tokens <= max_tokens:
                        merged = cls._merge_two_chunks(current, next_chunk)
                        merged_chunks.append(merged)
                        i += 2  # Skip both merged chunks
                        continue

                merged_chunks.append(current)
                i += 1

            # Step 3: Re-index reading order sequentially (0, 1, 2, ...) and update metadata
            optimized_chunks: List[KnowledgeChunk] = []
            for order, chk in enumerate(merged_chunks):
                chk.reading_order = order
                chk.metadata["reading_order"] = order
                TokenEstimator.enrich_chunk(chk)
                optimized_chunks.append(chk)

            logger.info(
                f"Completed chunk optimization: {len(chunks)} input chunks -> {len(optimized_chunks)} optimized chunks."
            )
            return optimized_chunks

        except Exception as e:
            logger.error(f"Chunk optimization failed: {e}")
            raise ChunkOptimizerError(f"Failed to optimize chunks: {str(e)}") from e

    @classmethod
    def _merge_two_chunks(cls, chunk1: KnowledgeChunk, chunk2: KnowledgeChunk) -> KnowledgeChunk:
        """Merges two adjacent KnowledgeChunk objects into a single chunk."""
        merged_content = f"{chunk1.content}\n\n{chunk2.content}".strip()
        merged_pages = sorted(list(set(chunk1.page_numbers + chunk2.page_numbers)))
        merged_tokens = TokenEstimator.estimate_tokens(merged_content)

        section_type = chunk1.section_type if chunk1.section_type == chunk2.section_type else "composite"

        merged_meta = {
            "document_id": chunk1.document_id,
            "page_numbers": merged_pages,
            "section_title": chunk1.section_title,
            "section_type": section_type,
            "hierarchy_level": min(chunk1.hierarchy_level, chunk2.hierarchy_level),
            "reading_order": chunk1.reading_order,
            "estimated_tokens": merged_tokens,
            "character_count": len(merged_content),
            "merged_from_count": 2,
        }

        return KnowledgeChunk(
            document_id=chunk1.document_id,
            page_numbers=merged_pages,
            section_title=chunk1.section_title,
            section_type=section_type,
            hierarchy_level=min(chunk1.hierarchy_level, chunk2.hierarchy_level),
            reading_order=chunk1.reading_order,
            content=merged_content,
            estimated_tokens=merged_tokens,
            metadata=merged_meta,
        )

    @classmethod
    def _split_oversized_chunk(cls, chunk: KnowledgeChunk, max_tokens: int) -> List[KnowledgeChunk]:
        """Splits an oversized chunk along natural paragraph line breaks."""
        lines = chunk.content.split("\n\n")
        if len(lines) <= 1:
            lines = chunk.content.split("\n")

        sub_chunks: List[KnowledgeChunk] = []
        accumulated_lines: List[str] = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            test_content = "\n\n".join(accumulated_lines + [line])
            test_tokens = TokenEstimator.estimate_tokens(test_content)

            if test_tokens > max_tokens and accumulated_lines:
                sub_content = "\n\n".join(accumulated_lines).strip()
                sub_tokens = TokenEstimator.estimate_tokens(sub_content)

                sub_chunks.append(
                    KnowledgeChunk(
                        document_id=chunk.document_id,
                        page_numbers=list(chunk.page_numbers),
                        section_title=chunk.section_title,
                        section_type=chunk.section_type,
                        hierarchy_level=chunk.hierarchy_level,
                        reading_order=chunk.reading_order,
                        content=sub_content,
                        estimated_tokens=sub_tokens,
                        metadata={
                            **chunk.metadata,
                            "estimated_tokens": sub_tokens,
                            "character_count": len(sub_content),
                            "split_chunk": True,
                        },
                    )
                )
                accumulated_lines = [line]
            else:
                accumulated_lines.append(line)

        if accumulated_lines:
            sub_content = "\n\n".join(accumulated_lines).strip()
            sub_tokens = TokenEstimator.estimate_tokens(sub_content)
            sub_chunks.append(
                KnowledgeChunk(
                    document_id=chunk.document_id,
                    page_numbers=list(chunk.page_numbers),
                    section_title=chunk.section_title,
                    section_type=chunk.section_type,
                    hierarchy_level=chunk.hierarchy_level,
                    reading_order=chunk.reading_order,
                    content=sub_content,
                    estimated_tokens=sub_tokens,
                    metadata={
                        **chunk.metadata,
                        "estimated_tokens": sub_tokens,
                        "character_count": len(sub_content),
                        "split_chunk": True,
                    },
                )
            )

        return sub_chunks
