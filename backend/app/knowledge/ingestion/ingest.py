"""Ingestion and Knowledge Structuring Pipeline Coordinator."""

from pathlib import Path
from typing import Optional, Union

from app.knowledge.analysis.hierarchy_builder import HierarchyBuilder
from app.knowledge.analysis.statistics import StatisticsGenerator
from app.knowledge.analysis.structure_analyzer import StructureAnalyzer
from app.knowledge.ingestion.cleaner import TextCleaner
from app.knowledge.ingestion.parser import DocumentParser
from app.knowledge.metadata.metadata_builder import MetadataBuilder
from app.knowledge.models.document import Document
from app.knowledge.models.structured_document import StructuredDocument
from app.utils.logging import logger


class IngestionPipeline:
    """Coordinates Phase 1 (Ingestion) and Phase 2 (Knowledge Structuring) pipelines."""

    def __init__(
        self,
        parser: Optional[DocumentParser] = None,
        cleaner: Optional[TextCleaner] = None,
        analyzer: Optional[StructureAnalyzer] = None,
        hierarchy_builder: Optional[HierarchyBuilder] = None,
        metadata_builder: Optional[MetadataBuilder] = None,
        statistics_generator: Optional[StatisticsGenerator] = None,
    ):
        """Initializes pipeline components."""
        self.parser = parser or DocumentParser()
        self.cleaner = cleaner or TextCleaner()
        self.analyzer = analyzer or StructureAnalyzer()
        self.hierarchy_builder = hierarchy_builder or HierarchyBuilder()
        self.metadata_builder = metadata_builder or MetadataBuilder()
        self.statistics_generator = statistics_generator or StatisticsGenerator()

    def process_pdf(self, file_path: Union[str, Path], document_id: Optional[str] = None) -> Document:
        """Executes Phase 1 ingestion pipeline on a PDF file: PDF -> Parser -> Cleaner -> Clean Document.

        Args:
            file_path (Union[str, Path]): Path to PDF file.
            document_id (Optional[str]): Optional custom document UUID identifier.

        Returns:
            Document: Cleaned Document object.
        """
        path = Path(file_path)
        logger.info(f"=== Starting Ingestion Pipeline (Phase 1) for '{path.name}' ===")

        raw_document = self.parser.parse(path, document_id=document_id)
        clean_document = self.cleaner.clean(raw_document)

        logger.info(
            f"=== Completed Ingestion Pipeline (Phase 1) for '{path.name}' === "
            f"[ID: {clean_document.id}, Pages: {clean_document.total_pages}, Chars: {clean_document.total_characters}]"
        )
        return clean_document

    def structure_document(self, clean_document: Document) -> StructuredDocument:
        """Executes Phase 2 Knowledge Structuring pipeline on a Clean Document object.

        Pipeline Steps:
            1. Structure Analyzer -> Extract typed sections (headings, paragraphs, lists, tables) in reading order.
            2. Hierarchy Builder -> Construct parent-child section relationships (H1 -> H2 -> H3 -> Paragraph).
            3. Metadata Builder -> Enrich every section with document, page, type, level, and order metadata.
            4. Statistics Generator -> Compute element counts and structural metrics.

        Args:
            clean_document (Document): Cleaned Document object from Phase 1.

        Returns:
            StructuredDocument: Fully structured document containing section list, hierarchy tree, and statistics.
        """
        logger.info(f"=== Starting Knowledge Structuring Pipeline (Phase 2) for '{clean_document.filename}' ===")

        # Step 1: Detect structural sections
        sections = self.analyzer.analyze(clean_document)

        # Step 2: Build document hierarchy parent-child links
        hierarchy = self.hierarchy_builder.build_hierarchy(sections)

        # Step 3: Enrich sections with structured metadata
        enriched_sections = self.metadata_builder.build_metadata(
            document_id=clean_document.id,
            sections=sections
        )

        # Step 4: Compute document statistics
        stats = self.statistics_generator.generate(
            total_pages=clean_document.total_pages,
            sections=enriched_sections
        )

        structured_doc = StructuredDocument(
            id=clean_document.id,
            filename=clean_document.filename,
            title=clean_document.title,
            file_type=clean_document.file_type,
            sections=enriched_sections,
            hierarchy=hierarchy,
            statistics=stats,
            metadata=dict(clean_document.metadata)
        )

        logger.info(
            f"=== Completed Knowledge Structuring Pipeline (Phase 2) for '{clean_document.filename}' === "
            f"[Sections: {len(structured_doc.sections)}, Root Hierarchy: {len(structured_doc.hierarchy)}]"
        )
        return structured_doc

    def process_pdf_to_structured(self, file_path: Union[str, Path], document_id: Optional[str] = None) -> StructuredDocument:
        """Executes full Phase 1 + Phase 2 pipeline on a PDF file.

        Args:
            file_path (Union[str, Path]): Path to PDF file.
            document_id (Optional[str]): Optional custom document UUID.

        Returns:
            StructuredDocument: Fully structured document object.
        """
        clean_doc = self.process_pdf(file_path, document_id=document_id)
        return self.structure_document(clean_doc)


def ingest_pdf(file_path: Union[str, Path], document_id: Optional[str] = None) -> Document:
    """Helper function to execute Phase 1 ingestion pipeline."""
    pipeline = IngestionPipeline()
    return pipeline.process_pdf(file_path, document_id=document_id)


def structure_pdf(file_path: Union[str, Path], document_id: Optional[str] = None) -> StructuredDocument:
    """Helper function to execute full Phase 1 + Phase 2 structuring pipeline."""
    pipeline = IngestionPipeline()
    return pipeline.process_pdf_to_structured(file_path, document_id=document_id)
