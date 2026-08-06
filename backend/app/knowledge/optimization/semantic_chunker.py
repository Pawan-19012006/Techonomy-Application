"""Semantic Chunker for grouping document sections by semantic boundaries."""

from typing import List, Set
from app.knowledge.exceptions import SemanticChunkerError
from app.knowledge.models.knowledge_chunk import KnowledgeChunk
from app.knowledge.models.section import Section
from app.knowledge.models.structured_document import StructuredDocument
from app.knowledge.optimization.token_estimator import TokenEstimator
from app.utils.logging import logger


class SemanticChunker:
    """Groups document sections into semantic KnowledgeChunk objects based on structural boundaries."""

    DEFAULT_MAX_TOKENS = 512
    DEFAULT_OVERLAP_TOKENS = 50

    @classmethod
    def chunk_document(
        cls,
        structured_doc: StructuredDocument,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
    ) -> List[KnowledgeChunk]:
        """Chunks a StructuredDocument into semantic KnowledgeChunk objects.

        Args:
            structured_doc (StructuredDocument): Structured Document object from Phase 2.
            max_tokens (int): Maximum estimated token budget per chunk.
            overlap_tokens (int): Overlap token count between adjacent chunks.

        Returns:
            List[KnowledgeChunk]: List of generated KnowledgeChunk objects.

        Raises:
            SemanticChunkerError: If semantic chunking fails.
        """
        if not structured_doc.sections:
            logger.warning(f"SemanticChunker received Document '{structured_doc.filename}' with 0 sections.")
            return []

        logger.info(
            f"Starting semantic chunking for '{structured_doc.filename}' "
            f"({len(structured_doc.sections)} sections, max_tokens={max_tokens})..."
        )

        try:
            chunks: List[KnowledgeChunk] = []
            chunk_order = 0

            # Active accumulator buffers
            accumulated_sections: List[Section] = []
            accumulated_text: str = ""
            current_governing_heading: str = structured_doc.title or "General"
            current_hierarchy_level: int = 1

            for idx, sec in enumerate(structured_doc.sections):
                # Update governing heading context if section is a heading
                if sec.section_type == "heading":
                    current_governing_heading = sec.title or sec.content
                    current_hierarchy_level = sec.level

                sec_tokens = TokenEstimator.estimate_tokens(sec.content)
                current_tokens = TokenEstimator.estimate_tokens(accumulated_text)

                # Check if adding this section exceeds max_tokens budget
                if accumulated_sections and (current_tokens + sec_tokens > max_tokens):
                    # Emit chunk for current accumulated sections
                    new_chunk = cls._create_chunk(
                        document_id=structured_doc.id,
                        sections=accumulated_sections,
                        governing_title=current_governing_heading,
                        hierarchy_level=current_hierarchy_level,
                        reading_order=chunk_order,
                    )
                    chunks.append(new_chunk)
                    chunk_order += 1

                    # Handle overlap: retain last section if within overlap budget
                    overlap_sections: List[Section] = []
                    if overlap_tokens > 0 and accumulated_sections:
                        last_sec = accumulated_sections[-1]
                        if TokenEstimator.estimate_tokens(last_sec.content) <= overlap_tokens:
                            overlap_sections.append(last_sec)

                    accumulated_sections = overlap_sections + [sec]
                    accumulated_text = "\n\n".join(s.content for s in accumulated_sections)
                else:
                    accumulated_sections.append(sec)
                    accumulated_text = "\n\n".join(s.content for s in accumulated_sections)

            # Flush final accumulated chunk
            if accumulated_sections:
                final_chunk = cls._create_chunk(
                    document_id=structured_doc.id,
                    sections=accumulated_sections,
                    governing_title=current_governing_heading,
                    hierarchy_level=current_hierarchy_level,
                    reading_order=chunk_order,
                )
                chunks.append(final_chunk)

            logger.info(
                f"Completed semantic chunking for '{structured_doc.filename}'. "
                f"Generated {len(chunks)} KnowledgeChunk objects."
            )
            return chunks

        except Exception as e:
            logger.error(f"Semantic chunking failed for '{structured_doc.filename}': {e}")
            raise SemanticChunkerError(f"Failed to chunk document '{structured_doc.filename}': {str(e)}") from e

    @classmethod
    def _create_chunk(
        cls,
        document_id: str,
        sections: List[Section],
        governing_title: str,
        hierarchy_level: int,
        reading_order: int,
    ) -> KnowledgeChunk:
        """Helper to construct a KnowledgeChunk from a list of grouped Section objects."""
        content = "\n\n".join(sec.content for sec in sections).strip()
        page_numbers: List[int] = sorted(list({sec.page_number for sec in sections}))

        # Primary section type classification
        sec_types: Set[str] = {sec.section_type for sec in sections}
        primary_type = list(sec_types)[0] if len(sec_types) == 1 else "composite"

        tokens = TokenEstimator.estimate_tokens(content)

        chunk_meta = {
            "document_id": document_id,
            "page_numbers": page_numbers,
            "section_title": governing_title,
            "section_type": primary_type,
            "hierarchy_level": hierarchy_level,
            "reading_order": reading_order,
            "section_count": len(sections),
            "estimated_tokens": tokens,
            "character_count": len(content),
        }

        return KnowledgeChunk(
            document_id=document_id,
            page_numbers=page_numbers,
            section_title=governing_title,
            section_type=primary_type,
            hierarchy_level=hierarchy_level,
            reading_order=reading_order,
            content=content,
            estimated_tokens=tokens,
            metadata=chunk_meta,
        )
