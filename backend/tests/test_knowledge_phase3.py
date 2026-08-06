"""Automated Pytest unit test suite for Knowledge Engine Phase 3 (Knowledge Optimization Engine)."""

from pathlib import Path
import pytest
from app.knowledge.ingestion.ingest import IngestionPipeline, chunk_pdf
from app.knowledge.models.chunk_statistics import ChunkStatistics
from app.knowledge.models.knowledge_chunk import KnowledgeChunk
from app.knowledge.optimization.chunk_optimizer import ChunkOptimizer
from app.knowledge.optimization.chunk_validator import ChunkValidator
from app.knowledge.optimization.semantic_chunker import SemanticChunker
from app.knowledge.optimization.token_estimator import TokenEstimator
from scripts.test_structure import generate_structured_sample_pdf


@pytest.fixture
def structured_pdf_path(tmp_path: Path) -> Path:
    """Fixture returning path to a generated structured sample PDF file."""
    pdf_file = tmp_path / "test_chunk_sample.pdf"
    return generate_structured_sample_pdf(pdf_file)


def test_token_estimator():
    """Tests TokenEstimator character heuristic token calculation."""
    text = "Hello world! This is a test for token estimation."
    tokens = TokenEstimator.estimate_tokens(text)
    assert tokens > 0
    assert tokens == int(round(len(text) / 4.0))

    empty_tokens = TokenEstimator.estimate_tokens("")
    assert empty_tokens == 0


def test_semantic_chunker(structured_pdf_path: Path):
    """Tests SemanticChunker document chunking."""
    sdoc = IngestionPipeline().process_pdf_to_structured(structured_pdf_path)
    chunks = SemanticChunker.chunk_document(sdoc, max_tokens=512)

    assert len(chunks) > 0
    for chunk in chunks:
        assert isinstance(chunk, KnowledgeChunk)
        assert chunk.document_id == sdoc.id
        assert len(chunk.page_numbers) > 0
        assert chunk.estimated_tokens > 0


def test_chunk_optimizer():
    """Tests ChunkOptimizer merging tiny chunks and splitting oversized chunks."""
    tiny1 = KnowledgeChunk(
        document_id="doc-1",
        page_numbers=[1],
        section_title="Title 1",
        section_type="paragraph",
        reading_order=0,
        content="Tiny paragraph 1.",
        estimated_tokens=5,
    )
    tiny2 = KnowledgeChunk(
        document_id="doc-1",
        page_numbers=[1],
        section_title="Title 1",
        section_type="paragraph",
        reading_order=1,
        content="Tiny paragraph 2.",
        estimated_tokens=5,
    )

    optimized = ChunkOptimizer.optimize([tiny1, tiny2], min_tokens=30, max_tokens=512)
    assert len(optimized) == 1
    assert "Tiny paragraph 1." in optimized[0].content
    assert "Tiny paragraph 2." in optimized[0].content
    assert optimized[0].reading_order == 0


def test_chunk_validator():
    """Tests ChunkValidator auditing constraints."""
    valid_chunk = KnowledgeChunk(
        document_id="doc-100",
        page_numbers=[1],
        section_title="Section Title",
        section_type="paragraph",
        reading_order=0,
        content="Valid content string for validation testing.",
        estimated_tokens=10,
        metadata={"document_id": "doc-100", "page_numbers": [1]},
    )
    invalid_chunk = KnowledgeChunk(
        document_id="",
        page_numbers=[],
        section_title="",
        section_type="paragraph",
        reading_order=1,
        content="",
        estimated_tokens=1000,
        metadata={},
    )

    valid_list, stats = ChunkValidator.validate_chunks([valid_chunk, invalid_chunk], max_tokens=512)

    assert len(valid_list) == 1
    assert valid_list[0].document_id == "doc-100"
    assert isinstance(stats, ChunkStatistics)
    assert stats.total_chunks == 1


def test_full_phase3_chunking_pipeline(structured_pdf_path: Path):
    """Tests end-to-end chunk_pdf pipeline."""
    chunks, stats = chunk_pdf(structured_pdf_path, max_tokens=512)

    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert stats.total_chunks == len(chunks)
    assert stats.total_tokens > 0
    assert stats.average_chunk_size > 0
