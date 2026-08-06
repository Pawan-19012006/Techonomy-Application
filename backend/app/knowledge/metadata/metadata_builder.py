"""Metadata Builder for enriching Section objects with structural metadata."""

from typing import List
from app.knowledge.exceptions import MetadataBuilderError
from app.knowledge.models.section import Section
from app.utils.logging import logger


class MetadataBuilder:
    """Enriches Section objects with structured metadata attributes."""

    @classmethod
    def build_metadata(cls, document_id: str, sections: List[Section]) -> List[Section]:
        """Attaches structured metadata dictionaries to every Section object in a document.

        Args:
            document_id (str): Parent document UUID identifier.
            sections (List[Section]): List of Section objects.

        Returns:
            List[Section]: Enriched Section objects.

        Raises:
            MetadataBuilderError: If metadata enrichment fails.
        """
        if not sections:
            return []

        logger.info(f"Building metadata for {len(sections)} sections in Document '{document_id}'...")

        try:
            for sec in sections:
                sec.metadata = {
                    "document_id": document_id,
                    "page_number": sec.page_number,
                    "section_title": sec.title or f"{sec.section_type.capitalize()} (Page {sec.page_number})",
                    "section_type": sec.section_type,
                    "hierarchy_level": sec.level,
                    "reading_order": sec.reading_order,
                    "character_count": sec.char_count,
                    "parent_id": sec.parent_id,
                    "has_parent": sec.parent_id is not None,
                    "child_count": len(sec.children_ids),
                }

            logger.info(f"Successfully enriched metadata for all {len(sections)} sections.")
            return sections

        except Exception as e:
            logger.error(f"Metadata enrichment failed for Document '{document_id}': {e}")
            raise MetadataBuilderError(f"Failed to build metadata for Document '{document_id}': {str(e)}") from e
