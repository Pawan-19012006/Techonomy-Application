"""Statistics Generator for computing quantitative structural document metrics."""

from typing import List
from app.knowledge.exceptions import StatisticsGeneratorError
from app.knowledge.models.section import Section
from app.knowledge.models.structured_document import DocumentStatistics
from app.utils.logging import logger


class StatisticsGenerator:
    """Calculates structural metrics and element counts across Document Section objects."""

    @classmethod
    def generate(cls, total_pages: int, sections: List[Section]) -> DocumentStatistics:
        """Computes DocumentStatistics from extracted Section objects.

        Args:
            total_pages (int): Total document page count.
            sections (List[Section]): List of extracted Section objects.

        Returns:
            DocumentStatistics: Computed document statistics object.

        Raises:
            StatisticsGeneratorError: If statistics computation fails.
        """
        logger.info(f"Generating document statistics for {len(sections)} sections across {total_pages} pages...")

        try:
            total_sections = len(sections)
            headings_count = sum(1 for sec in sections if sec.section_type == "heading")
            paragraphs_count = sum(1 for sec in sections if sec.section_type == "paragraph")
            lists_count = sum(1 for sec in sections if sec.section_type == "list")
            tables_count = sum(1 for sec in sections if sec.section_type == "table")

            total_chars = sum(sec.char_count for sec in sections)
            avg_length = round(total_chars / total_sections, 2) if total_sections > 0 else 0.0

            stats = DocumentStatistics(
                total_pages=total_pages,
                total_headings=headings_count,
                total_sections=total_sections,
                total_paragraphs=paragraphs_count,
                total_lists=lists_count,
                total_tables=tables_count,
                total_characters=total_chars,
                average_section_length=avg_length,
            )

            logger.info(
                f"Generated DocumentStatistics: Pages={stats.total_pages}, Sections={stats.total_sections}, "
                f"Headings={stats.total_headings}, Paragraphs={stats.total_paragraphs}, Lists={stats.total_lists}, "
                f"Tables={stats.total_tables}, Total Chars={stats.total_characters}, Avg Length={stats.average_section_length}."
            )
            return stats

        except Exception as e:
            logger.error(f"Statistics generation failed: {e}")
            raise StatisticsGeneratorError(f"Failed to generate document statistics: {str(e)}") from e
