"""Ingestion, Knowledge Structuring, Optimization, and Indexing Pipeline Coordinator."""

from pathlib import Path
from typing import List, Optional, Tuple, Union

from app.knowledge.analysis.hierarchy_builder import HierarchyBuilder
from app.knowledge.analysis.statistics import StatisticsGenerator
from app.knowledge.analysis.structure_analyzer import StructureAnalyzer
from app.knowledge.indexing.index_manager import IndexManager
from app.knowledge.ingestion.cleaner import TextCleaner
from app.knowledge.ingestion.parser import DocumentParser
from app.knowledge.metadata.metadata_builder import MetadataBuilder
from app.knowledge.models.chunk_statistics import ChunkStatistics
from app.knowledge.models.document import Document
from app.knowledge.models.index_result import IndexResult
from app.knowledge.models.knowledge_chunk import KnowledgeChunk
from app.knowledge.models.structured_document import StructuredDocument
from app.knowledge.optimization.chunk_optimizer import ChunkOptimizer
from app.knowledge.optimization.chunk_validator import ChunkValidator
from app.knowledge.optimization.semantic_chunker import SemanticChunker
from app.knowledge.optimization.token_estimator import TokenEstimator
from app.utils.logging import logger


class IngestionPipeline:
    """Coordinates Phase 1 (Ingestion), Phase 2 (Knowledge Structuring), Phase 3 (Knowledge Optimization), and Phase 4 (Knowledge Indexing) pipelines."""

    def __init__(
        self,
        parser: Optional[DocumentParser] = None,
        cleaner: Optional[TextCleaner] = None,
        analyzer: Optional[StructureAnalyzer] = None,
        hierarchy_builder: Optional[HierarchyBuilder] = None,
        metadata_builder: Optional[MetadataBuilder] = None,
        statistics_generator: Optional[StatisticsGenerator] = None,
        semantic_chunker: Optional[SemanticChunker] = None,
        chunk_optimizer: Optional[ChunkOptimizer] = None,
        chunk_validator: Optional[ChunkValidator] = None,
        token_estimator: Optional[TokenEstimator] = None,
        index_manager: Optional[IndexManager] = None,
    ):
        """Initializes pipeline components."""
        self.parser = parser or DocumentParser()
        self.cleaner = cleaner or TextCleaner()
        self.analyzer = analyzer or StructureAnalyzer()
        self.hierarchy_builder = hierarchy_builder or HierarchyBuilder()
        self.metadata_builder = metadata_builder or MetadataBuilder()
        self.statistics_generator = statistics_generator or StatisticsGenerator()
        self.semantic_chunker = semantic_chunker or SemanticChunker()
        self.chunk_optimizer = chunk_optimizer or ChunkOptimizer()
        self.chunk_validator = chunk_validator or ChunkValidator()
        self.token_estimator = token_estimator or TokenEstimator()
        self.index_manager = index_manager or IndexManager()

    def process_pdf(self, file_path: Union[str, Path], document_id: Optional[str] = None) -> Document:
        """Executes Phase 1 ingestion pipeline on a PDF file: PDF -> Parser -> Cleaner -> Clean Document."""
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
        """Executes Phase 2 Knowledge Structuring pipeline on a Clean Document object."""
        logger.info(f"=== Starting Knowledge Structuring Pipeline (Phase 2) for '{clean_document.filename}' ===")

        sections = self.analyzer.analyze(clean_document)
        hierarchy = self.hierarchy_builder.build_hierarchy(sections)
        enriched_sections = self.metadata_builder.build_metadata(
            document_id=clean_document.id,
            sections=sections
        )
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

    def optimize_chunks(
        self,
        structured_doc: StructuredDocument,
        max_tokens: int = 512,
        min_tokens: int = 30,
        overlap_tokens: int = 50,
    ) -> Tuple[List[KnowledgeChunk], ChunkStatistics]:
        """Executes Phase 3 Knowledge Optimization pipeline on a StructuredDocument object."""
        logger.info(f"=== Starting Knowledge Optimization Pipeline (Phase 3) for '{structured_doc.filename}' ===")

        raw_chunks = self.semantic_chunker.chunk_document(
            structured_doc,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
        )

        optimized_chunks = self.chunk_optimizer.optimize(
            raw_chunks,
            min_tokens=min_tokens,
            max_tokens=max_tokens,
        )

        valid_chunks, chunk_stats = self.chunk_validator.validate_chunks(
            optimized_chunks,
            max_tokens=max_tokens,
        )

        logger.info(
            f"=== Completed Knowledge Optimization Pipeline (Phase 3) for '{structured_doc.filename}' === "
            f"[Chunks: {chunk_stats.total_chunks}, Total Tokens: {chunk_stats.total_tokens}, Avg Size: {chunk_stats.average_chunk_size} chars]"
        )
        return valid_chunks, chunk_stats

    def index_document_chunks(
        self,
        chunks: List[KnowledgeChunk],
        document_name: Optional[str] = None,
        recreate_collection: bool = False,
    ) -> IndexResult:
        """Executes Phase 4 Knowledge Indexing pipeline: Embedder -> Normalizer -> Payload -> Qdrant."""
        logger.info(f"=== Starting Knowledge Indexing Pipeline (Phase 4) for {len(chunks)} chunks ===")
        result = self.index_manager.index_chunks(
            chunks=chunks,
            document_name=document_name,
            recreate_collection=recreate_collection,
        )
        return result

    def process_pdf_to_structured(self, file_path: Union[str, Path], document_id: Optional[str] = None) -> StructuredDocument:
        """Executes Phase 1 + Phase 2 pipeline on a PDF file."""
        clean_doc = self.process_pdf(file_path, document_id=document_id)
        return self.structure_document(clean_doc)

    def process_pdf_to_chunks(
        self,
        file_path: Union[str, Path],
        document_id: Optional[str] = None,
        max_tokens: int = 512,
    ) -> Tuple[List[KnowledgeChunk], ChunkStatistics]:
        """Executes Phase 1 + 2 + 3 pipeline on a PDF file."""
        structured_doc = self.process_pdf_to_structured(file_path, document_id=document_id)
        return self.optimize_chunks(structured_doc, max_tokens=max_tokens)

    def process_pdf_to_index(
        self,
        file_path: Union[str, Path],
        document_id: Optional[str] = None,
        max_tokens: int = 512,
        recreate_collection: bool = False,
    ) -> IndexResult:
        """Executes full end-to-end pipeline (Phase 1 + 2 + 3 + 4) on a PDF file.

        Args:
            file_path (Union[str, Path]): Path to PDF file.
            document_id (Optional[str]): Optional custom document UUID.
            max_tokens (int): Max token budget ceiling per chunk.
            recreate_collection (bool): Recreate collection before indexing.

        Returns:
            IndexResult: Indexing result object.
        """
        path = Path(file_path)
        chunks, _ = self.process_pdf_to_chunks(path, document_id=document_id, max_tokens=max_tokens)
        return self.index_document_chunks(
            chunks=chunks,
            document_name=path.name,
            recreate_collection=recreate_collection,
        )


def ingest_pdf(file_path: Union[str, Path], document_id: Optional[str] = None) -> Document:
    """Helper function to execute Phase 1 ingestion pipeline."""
    pipeline = IngestionPipeline()
    return pipeline.process_pdf(file_path, document_id=document_id)


def structure_pdf(file_path: Union[str, Path], document_id: Optional[str] = None) -> StructuredDocument:
    """Helper function to execute Phase 1 + Phase 2 structuring pipeline."""
    pipeline = IngestionPipeline()
    return pipeline.process_pdf_to_structured(file_path, document_id=document_id)


def chunk_pdf(
    file_path: Union[str, Path],
    document_id: Optional[str] = None,
    max_tokens: int = 512,
) -> Tuple[List[KnowledgeChunk], ChunkStatistics]:
    """Helper function to execute Phase 1 + 2 + 3 chunking pipeline."""
    pipeline = IngestionPipeline()
    return pipeline.process_pdf_to_chunks(file_path, document_id=document_id, max_tokens=max_tokens)


def index_pdf(
    file_path: Union[str, Path],
    document_id: Optional[str] = None,
    max_tokens: int = 512,
    recreate_collection: bool = False,
) -> IndexResult:
    """Helper function to execute full end-to-end (Phase 1 + 2 + 3 + 4) indexing pipeline."""
    pipeline = IngestionPipeline()
    return pipeline.process_pdf_to_index(
        file_path,
        document_id=document_id,
        max_tokens=max_tokens,
        recreate_collection=recreate_collection,
    )
