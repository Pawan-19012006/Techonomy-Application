"""Automated Pytest unit test suite for Knowledge Engine Phase 1."""

from pathlib import Path
import pytest
from app.knowledge.exceptions import PDFLoaderError, DocumentParserError
from app.knowledge.ingestion.cleaner import TextCleaner
from app.knowledge.ingestion.ingest import IngestionPipeline, ingest_pdf
from app.knowledge.ingestion.parser import DocumentParser
from app.knowledge.loaders.pdf_loader import PDFLoader
from app.knowledge.models.chunk import Chunk
from app.knowledge.models.document import Document
from app.knowledge.models.page import Page
from scripts.test_parser import generate_sample_pdf


@pytest.fixture
def sample_pdf_path(tmp_path: Path) -> Path:
    """Fixture returning path to a generated sample PDF file."""
    pdf_file = tmp_path / "test_sample.pdf"
    return generate_sample_pdf(pdf_file)


def test_models_instantiation():
    """Tests Page, Document, and Chunk domain models instantiation and properties."""
    page1 = Page(page_number=1, text="Hello World", metadata={"width": 100})
    assert page1.page_number == 1
    assert page1.char_count == 11
    assert page1.metadata["width"] == 100

    doc = Document(
        filename="test.pdf",
        title="Test Document",
        file_type="pdf",
        total_pages=1,
        pages=[page1]
    )
    assert doc.filename == "test.pdf"
    assert doc.total_characters == 11
    assert doc.pages[0].page_number == 1

    chunk = Chunk(
        document_id=doc.id,
        page_number=1,
        content="Hello World",
        chunk_index=0
    )
    assert chunk.document_id == doc.id
    assert chunk.page_number == 1
    assert chunk.content == "Hello World"


def test_pdf_loader(sample_pdf_path: Path):
    """Tests PyMuPDF PDFLoader page extraction."""
    pages = PDFLoader.load(sample_pdf_path)
    assert len(pages) == 3
    assert pages[0].page_number == 1
    assert pages[1].page_number == 2
    assert pages[2].page_number == 3
    assert "Techonomy Enterprise Knowledge Intelligence Platform" in pages[0].text


def test_pdf_loader_invalid_file(tmp_path: Path):
    """Tests PDFLoader error handling for non-existent and corrupt files."""
    missing_file = tmp_path / "non_existent.pdf"
    with pytest.raises(PDFLoaderError):
        PDFLoader.load(missing_file)

    invalid_pdf = tmp_path / "corrupt.pdf"
    invalid_pdf.write_text("This is not a PDF content")
    with pytest.raises(PDFLoaderError):
        PDFLoader.load(invalid_pdf)


def test_document_parser(sample_pdf_path: Path):
    """Tests DocumentParser orchestration."""
    doc = DocumentParser.parse(sample_pdf_path)
    assert doc.filename == "test_sample.pdf"
    assert doc.file_type == "pdf"
    assert doc.total_pages == 3
    assert len(doc.pages) == 3


def test_text_cleaner(sample_pdf_path: Path):
    """Tests TextCleaner whitespace normalization and header/footer removal."""
    raw_doc = DocumentParser.parse(sample_pdf_path)
    clean_doc = TextCleaner.clean(raw_doc)

    assert clean_doc.total_pages == 3
    # Verify repeated header line was stripped from cleaned pages
    assert "Techonomy Enterprise Knowledge Intelligence Platform" not in clean_doc.pages[0].text
    assert "Confidential Corporate Report 2026" not in clean_doc.pages[0].text
    # Verify meaningful content preserved
    assert "Section 1: Executive Summary" in clean_doc.pages[0].text


def test_ingest_pipeline_full_flow(sample_pdf_path: Path):
    """Tests full end-to-end Phase 1 ingestion pipeline."""
    clean_doc = ingest_pdf(sample_pdf_path)
    assert isinstance(clean_doc, Document)
    assert clean_doc.filename == "test_sample.pdf"
    assert clean_doc.total_pages == 3
    assert clean_doc.metadata.get("cleaned") is True
