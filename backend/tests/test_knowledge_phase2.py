"""Automated Pytest unit test suite for Knowledge Engine Phase 2 (Knowledge Structuring Engine)."""

from pathlib import Path
import pytest
from app.knowledge.analysis.hierarchy_builder import HierarchyBuilder
from app.knowledge.analysis.statistics import StatisticsGenerator
from app.knowledge.analysis.structure_analyzer import StructureAnalyzer
from app.knowledge.ingestion.ingest import IngestionPipeline, structure_pdf
from app.knowledge.ingestion.parser import DocumentParser
from app.knowledge.metadata.metadata_builder import MetadataBuilder
from app.knowledge.models.section import Section
from app.knowledge.models.structured_document import DocumentStatistics, StructuredDocument
from scripts.test_structure import generate_structured_sample_pdf


@pytest.fixture
def structured_pdf_path(tmp_path: Path) -> Path:
    """Fixture returning path to a generated structured sample PDF file."""
    pdf_file = tmp_path / "test_structured_sample.pdf"
    return generate_structured_sample_pdf(pdf_file)


def test_phase2_models():
    """Tests Section, DocumentStatistics, and StructuredDocument instantiation."""
    sec = Section(
        title="Executive Summary",
        section_type="heading",
        level=1,
        content="Section 1: Executive Summary",
        page_number=1,
        reading_order=0,
    )
    assert sec.title == "Executive Summary"
    assert sec.section_type == "heading"
    assert sec.level == 1
    assert sec.char_count == len("Section 1: Executive Summary")

    stats = DocumentStatistics(
        total_pages=2,
        total_headings=4,
        total_sections=10,
        total_paragraphs=4,
        total_lists=1,
        total_tables=1,
        total_characters=500,
        average_section_length=50.0,
    )
    assert stats.total_pages == 2
    assert stats.total_headings == 4
    assert stats.average_section_length == 50.0

    sdoc = StructuredDocument(
        filename="report.pdf",
        title="Report Title",
        file_type="pdf",
        sections=[sec],
        hierarchy=[sec],
        statistics=stats,
    )
    assert sdoc.filename == "report.pdf"
    assert len(sdoc.sections) == 1
    assert len(sdoc.hierarchy) == 1


def test_structure_analyzer(structured_pdf_path: Path):
    """Tests StructureAnalyzer detection of headings, lists, and paragraphs."""
    clean_doc = IngestionPipeline().process_pdf(structured_pdf_path)
    sections = StructureAnalyzer.analyze(clean_doc)

    assert len(sections) > 0
    # Verify reading order is 0-indexed and sequential
    orders = [s.reading_order for s in sections]
    assert orders == list(range(len(sections)))

    # Verify section type classifications
    sec_types = {s.section_type for s in sections}
    assert "heading" in sec_types or "paragraph" in sec_types


def test_hierarchy_builder():
    """Tests HierarchyBuilder parent-child linking."""
    sec_h1 = Section(
        id="sec-1",
        title="Main Heading",
        section_type="heading",
        level=1,
        content="Main Heading",
        page_number=1,
        reading_order=0,
    )
    sec_h2 = Section(
        id="sec-2",
        title="Sub Heading",
        section_type="heading",
        level=2,
        content="Sub Heading",
        page_number=1,
        reading_order=1,
    )
    sec_p = Section(
        id="sec-3",
        title="Paragraph",
        section_type="paragraph",
        level=4,
        content="Body paragraph text.",
        page_number=1,
        reading_order=2,
    )

    flat_sections = [sec_h1, sec_h2, sec_p]
    roots = HierarchyBuilder.build_hierarchy(flat_sections)

    assert len(roots) == 1
    assert roots[0].id == "sec-1"
    assert sec_h2.parent_id == "sec-1"
    assert "sec-2" in sec_h1.children_ids
    assert sec_p.parent_id == "sec-2"
    assert "sec-3" in sec_h2.children_ids


def test_metadata_builder():
    """Tests MetadataBuilder enrichment of Section metadata."""
    sec = Section(
        id="sec-1",
        title="Test Heading",
        section_type="heading",
        level=1,
        content="Test Heading Content",
        page_number=2,
        reading_order=3,
    )
    enriched = MetadataBuilder.build_metadata(document_id="doc-123", sections=[sec])

    assert len(enriched) == 1
    meta = enriched[0].metadata
    assert meta["document_id"] == "doc-123"
    assert meta["page_number"] == 2
    assert meta["section_title"] == "Test Heading"
    assert meta["section_type"] == "heading"
    assert meta["hierarchy_level"] == 1
    assert meta["reading_order"] == 3
    assert meta["character_count"] == len("Test Heading Content")


def test_statistics_generator():
    """Tests StatisticsGenerator metrics calculations."""
    sec1 = Section(title="H1", section_type="heading", level=1, content="Heading 1", page_number=1, reading_order=0)
    sec2 = Section(title="P1", section_type="paragraph", level=4, content="Paragraph Content 1", page_number=1, reading_order=1)
    sec3 = Section(title="L1", section_type="list", level=3, content="- Item 1\n- Item 2", page_number=1, reading_order=2)

    stats = StatisticsGenerator.generate(total_pages=1, sections=[sec1, sec2, sec3])
    assert stats.total_pages == 1
    assert stats.total_sections == 3
    assert stats.total_headings == 1
    assert stats.total_paragraphs == 1
    assert stats.total_lists == 1
    assert stats.total_tables == 0
    assert stats.total_characters == (len(sec1.content) + len(sec2.content) + len(sec3.content))
    assert stats.average_section_length > 0


def test_full_phase2_structuring_pipeline(structured_pdf_path: Path):
    """Tests end-to-end structure_pdf pipeline."""
    structured_doc = structure_pdf(structured_pdf_path)

    assert isinstance(structured_doc, StructuredDocument)
    assert structured_doc.filename == "test_structured_sample.pdf"
    assert len(structured_doc.sections) > 0
    assert len(structured_doc.hierarchy) > 0
    assert structured_doc.statistics.total_sections == len(structured_doc.sections)
    assert structured_doc.statistics.total_pages == 2
