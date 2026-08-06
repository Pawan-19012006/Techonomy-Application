"""Automated Pytest unit test suite for Knowledge Engine Phase 5 (Knowledge Retrieval Engine)."""

from pathlib import Path
import pytest
from app.config import settings
from app.knowledge.exceptions import QueryProcessorError
from app.knowledge.indexing.qdrant_client import QdrantClientWrapper
from app.knowledge.ingestion.ingest import index_pdf
from app.knowledge.models.context_package import ContextPackage
from app.knowledge.models.processed_query import ProcessedQuery
from app.knowledge.models.retrieval_result import RetrievalResult
from app.knowledge.models.search_result import SearchResult
from app.knowledge.retrieval.context_builder import ContextBuilder
from app.knowledge.retrieval.query_embedder import QueryEmbedder
from app.knowledge.retrieval.query_processor import QueryProcessor
from app.knowledge.retrieval.reranker import Reranker
from app.knowledge.retrieval.retrieval_pipeline import RetrievalPipeline, retrieve_context
from app.knowledge.retrieval.search_filters import SearchFilters
from app.knowledge.retrieval.vector_search import VectorSearch
from scripts.test_structure import generate_structured_sample_pdf


@pytest.fixture
def sample_search_results() -> list[SearchResult]:
    """Fixture returning sample SearchResult matches."""
    return [
        SearchResult(
            chunk_id="chk-1",
            document_id="doc-100",
            document_name="annual_report.pdf",
            score=0.85,
            content="Total Revenue for fiscal year 2026 reached $500 Million.",
            page_numbers=[42],
            section_title="Financial Highlights",
            section_type="heading",
            hierarchy_level=2,
            reading_order=0,
            estimated_tokens=20,
        ),
        SearchResult(
            chunk_id="chk-2",
            document_id="doc-100",
            document_name="annual_report.pdf",
            score=0.78,
            content="Revenue from operations increased by 15% year over year.",
            page_numbers=[43],
            section_title="Revenue Analysis",
            section_type="paragraph",
            hierarchy_level=3,
            reading_order=1,
            estimated_tokens=18,
        ),
        SearchResult(
            chunk_id="chk-3",
            document_id="doc-200",
            document_name="financial_statement.pdf",
            score=0.72,
            content="Operating profit margins expanded by 250 basis points.",
            page_numbers=[17],
            section_title="Profitability Notes",
            section_type="paragraph",
            hierarchy_level=3,
            reading_order=2,
            estimated_tokens=16,
        ),
    ]


def test_query_processor():
    """Tests QueryProcessor validation and normalization."""
    processor = QueryProcessor(max_length=2000)

    # Test valid query
    pq = processor.process("  What was the total revenue growth in 2026?   ")
    assert pq.original_query == "  What was the total revenue growth in 2026?   "
    assert pq.normalized_query == "What was the total revenue growth in 2026?"
    assert pq.word_count == 8
    assert pq.is_valid is True

    # Test empty query error
    with pytest.raises(QueryProcessorError):
        processor.process("   ")


def test_query_embedder():
    """Tests QueryEmbedder embedding generation."""
    processor = QueryProcessor()
    embedder = QueryEmbedder()

    pq = processor.process("What is the company revenue?")
    vec = embedder.embed_query(pq)

    assert len(vec) == 384
    assert embedder.get_dimension() == 384


def test_search_filters():
    """Tests SearchFilters construction."""
    filters = SearchFilters(
        document_id="doc-100",
        page_numbers=[42, 43],
        section_type="heading",
        minimum_similarity=0.70,
    )
    q_filter = filters.to_qdrant_filter()
    assert q_filter is not None
    assert len(q_filter.must) == 3


def test_reranker(sample_search_results: list[SearchResult]):
    """Tests Reranker hybrid scoring and keyword boosting."""
    processor = QueryProcessor()
    pq = processor.process("What is the total revenue?")

    reranker = Reranker(top_n=2)
    reranked = reranker.rerank(sample_search_results, pq)

    assert len(reranked) == 2
    # Verify reranked scores are sorted descending
    assert reranked[0].score >= reranked[1].score
    # Verify title match on 'Financial Highlights' / 'Revenue' boosted top match
    assert "revenue" in reranked[0].content.lower() or "revenue" in reranked[0].section_title.lower()


def test_context_builder(sample_search_results: list[SearchResult]):
    """Tests ContextBuilder deduplication, citation formatting, and token budget."""
    builder = ContextBuilder(token_budget=200)
    package = builder.build_context(sample_search_results)

    assert isinstance(package, ContextPackage)
    assert package.chunks_used > 0
    assert len(package.sources) > 0
    assert "annual_report.pdf Page 42" in package.sources or "annual_report.pdf Page 43" in package.sources
    assert package.estimated_tokens <= 200


def test_full_phase5_retrieval_pipeline(tmp_path: Path):
    """Tests full end-to-end RetrievalPipeline on indexed PDF."""
    pdf_file = tmp_path / "test_retrieval_sample.pdf"
    generate_structured_sample_pdf(pdf_file)

    # Index document first
    index_pdf(pdf_file, recreate_collection=True)

    # Execute retrieval
    res = retrieve_context("What is the corporate report about?", top_k=5, top_n=3)

    assert isinstance(res, RetrievalResult)
    assert res.processed_query.is_valid is True
    assert res.embedding_dimension == 384
    assert res.top_k_searched > 0
    assert res.top_n_reranked > 0
    assert len(res.context_package.sources) > 0
    assert res.processing_time > 0.0
