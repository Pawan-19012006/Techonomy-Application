"""Ingestion Pipeline Coordinator for processing documents into clean Document objects."""

from pathlib import Path
from typing import Optional, Union

from app.knowledge.ingestion.cleaner import TextCleaner
from app.knowledge.ingestion.parser import DocumentParser
from app.knowledge.models.document import Document
from app.utils.logging import logger


class IngestionPipeline:
    """Coordinates Phase 1 ingestion pipeline: PDF -> Parser -> Cleaner -> Clean Document."""

    def __init__(self, parser: Optional[DocumentParser] = None, cleaner: Optional[TextCleaner] = None):
        """Initializes pipeline components.

        Args:
            parser (Optional[DocumentParser]): Document parser instance.
            cleaner (Optional[TextCleaner]): Text cleaner instance.
        """
        self.parser = parser or DocumentParser()
        self.cleaner = cleaner or TextCleaner()

    def process_pdf(self, file_path: Union[str, Path], document_id: Optional[str] = None) -> Document:
        """Executes full Phase 1 ingestion pipeline on a PDF file.

        Pipeline Steps:
            1. Parse PDF using PDFLoader -> Raw Document object with Page list.
            2. Normalize whitespace and clean noise using TextCleaner -> Clean Document object.

        Args:
            file_path (Union[str, Path]): Path to PDF file.
            document_id (Optional[str]): Optional custom document UUID identifier.

        Returns:
            Document: Cleaned Document object ready for downstream indexing.
        """
        path = Path(file_path)
        logger.info(f"=== Starting Ingestion Pipeline for '{path.name}' ===")

        # Step 1: Parse PDF to raw Document object
        raw_document = self.parser.parse(path, document_id=document_id)

        # Step 2: Clean Document text and whitespace
        clean_document = self.cleaner.clean(raw_document)

        logger.info(
            f"=== Completed Ingestion Pipeline for '{path.name}' === "
            f"[ID: {clean_document.id}, Pages: {clean_document.total_pages}, Chars: {clean_document.total_characters}]"
        )
        return clean_document


def ingest_pdf(file_path: Union[str, Path], document_id: Optional[str] = None) -> Document:
    """Helper function to execute the PDF ingestion pipeline.

    Args:
        file_path (Union[str, Path]): Path to PDF file.
        document_id (Optional[str]): Optional custom document UUID identifier.

    Returns:
        Document: Clean Document object.
    """
    pipeline = IngestionPipeline()
    return pipeline.process_pdf(file_path, document_id=document_id)
