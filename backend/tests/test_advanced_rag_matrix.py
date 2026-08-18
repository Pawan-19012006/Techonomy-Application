"""Comprehensive RAG Intelligence & Analytical Matrix Test Suite.

Tests cover:
- Temporal Resolution (last year, last month, latest quarter, FY25/FY26)
- Concept & Synonym Expansion (profitability, working capital, sales, customer retention)
- Instruction-Guided Multi-Query Retrieval & Evidence Coverage
- Iterative Second-Pass Targeted Retrieval
- Derived Calculations & Derived Analytical Results
- Citation Integrity & Evidence Isolation (Company ONLY, zero instruction leaks)
- Transparent Refusal on Genuine Lack of Evidence
"""

import pytest
from app.config import settings
from app.knowledge.indexing.collection_manager import CollectionManager
from app.knowledge.ingestion.ingest import ingest_company_pdf, ingest_instruction_pdf
from app.knowledge.rag.chat_service import ChatService
from app.knowledge.rag.prompt_builder import PromptBuilder
from app.knowledge.retrieval.concept_expander import ConceptExpander
from app.knowledge.retrieval.evidence_checker import EvidenceChecker
from app.knowledge.retrieval.instruction_planner import InstructionPlanner
from app.knowledge.retrieval.retrieval_pipeline import RetrievalPipeline
from app.knowledge.retrieval.temporal_resolver import TemporalResolver


@pytest.fixture(scope="module", autouse=True)
def ensure_populated_collections():
    """Ensures Qdrant collections contain data for integration tests."""
    company_cm = CollectionManager(collection_name=settings.QDRANT_COMPANY_COLLECTION_NAME)
    comp_info = company_cm.get_info()
    comp_cnt = comp_info.get("points_count", 0) if isinstance(comp_info, dict) else 0

    if comp_cnt == 0:
        company_dir = settings.BASE_DIR / "data" / "documents" / "company"
        for pdf in sorted(list(company_dir.glob("*.pdf"))):
            ingest_company_pdf(pdf)

    inst_cm = CollectionManager(collection_name=settings.QDRANT_INSTRUCTION_COLLECTION_NAME)
    inst_info = inst_cm.get_info()
    inst_cnt = inst_info.get("points_count", 0) if isinstance(inst_info, dict) else 0

    if inst_cnt == 0:
        inst_dir = settings.BASE_DIR / "data" / "documents" / "instructions"
        for pdf in sorted(list(inst_dir.glob("*.pdf"))):
            ingest_instruction_pdf(pdf)


def test_temporal_resolver_relative_expressions():
    """Test 1: TemporalResolver parses 'last year', 'this year', 'last month', and 'multi-year'."""
    resolver = TemporalResolver()

    t1 = resolver.resolve("What was revenue last year?")
    assert t1.original_reference == "last year"
    assert "FY 2024-25" in t1.resolved_periods

    t2 = resolver.resolve("What are the revenue for last month?")
    assert t2.original_reference == "last month"
    assert t2.comparison_type == "mom"

    t3 = resolver.resolve("Compare revenue across all available financial years")
    assert t3.comparison_type == "multi_year"
    assert len(t3.resolved_periods) >= 3


def test_concept_expander_synonyms():
    """Test 2: ConceptExpander expands profitability, working capital, and sales into metric terms."""
    expander = ConceptExpander()

    c1 = expander.expand("How has profitability changed?")
    assert "profitability" in c1.primary_concepts or any("profit" in term for term in c1.expanded_terms)
    assert len(c1.generated_subqueries) > 0

    c2 = expander.expand("What are the major working capital concerns?")
    assert any("inventory" in term or "receivable" in term for term in c1.expanded_terms + c2.expanded_terms)
    assert len(c2.generated_subqueries) > 0


def test_instruction_planner_rich_plan():
    """Test 3: InstructionPlanner generates a comprehensive RetrievalPlan with temporal & concept fields."""
    planner = InstructionPlanner()
    query = "How has the company's profitability changed across the available reporting periods?"

    guidance = planner.retrieve_instruction_guidance(query)
    plan = planner.create_retrieval_plan(query, guidance)

    assert plan.intent == "financial_analysis"
    assert plan.temporal_reference is not None or len(plan.company_search_queries) > 2
    assert "growth_percentage_calculation" in plan.analytical_operations
    assert len(plan.company_search_queries) >= 3


def test_evidence_checker_and_iterative_retrieval():
    """Test 4: EvidenceChecker detects coverage completeness and triggers fallback queries if metrics missing."""
    checker = EvidenceChecker()

    # Empty candidate list triggers fallback subqueries
    report = checker.check_coverage(candidates=[], required_metrics=["revenue", "net_profit"], intent="financial_analysis")
    assert report.is_sufficient is False
    assert len(report.targeted_fallback_queries) > 0
    assert any("revenue" in q.lower() for q in report.targeted_fallback_queries)


def test_retrieval_pipeline_multi_domain():
    """Test 5: RetrievalPipeline returns company-only reranked results for complex queries."""
    pipeline = RetrievalPipeline()
    query = "What are the major working-capital concerns and how do they impact cash position?"

    result = pipeline.retrieve(query=query)
    assert hasattr(result, "reranked_results")
    assert len(result.reranked_results) > 0

    for chk in result.reranked_results:
        doc_type = getattr(chk, "document_type", "company")
        vis = getattr(chk, "visibility", "user_visible")
        assert doc_type == "company", f"Leaked instruction document: {chk.document_name}"
        assert vis == "user_visible"


def test_chat_service_sources_isolation():
    """Test 6: ChatService._extract_sources strictly enforces company-only citations and omits on refusal."""
    service = ChatService()

    # Case A: Answer is a refusal
    refusal_answer = "The available company documents do not contain sufficient evidence to answer this question."
    sources_refusal = service._extract_sources(retrieval_result=None, answer=refusal_answer)
    assert len(sources_refusal) == 0

    # Case B: Answer contains company citations
    class MockChunk:
        document_name = "1.pdf"
        page_numbers = [19]
        document_type = "company"
        visibility = "user_visible"

    class MockRetrievalResult:
        reranked_results = [MockChunk()]

    valid_answer = "Annual revenue in FY 2025-26 reached ₹8.36 Crore."
    sources_valid = service._extract_sources(retrieval_result=MockRetrievalResult(), answer=valid_answer)
    assert len(sources_valid) == 1
    assert sources_valid[0].document == "1.pdf"
    assert sources_valid[0].page == 19


def test_unsupported_query_transparent_refusal():
    """Test 7: Query about non-existent topic returns transparent refusal without hallucinating facts."""
    service = ChatService()
    query = "What was the company's cryptocurrency trading profit in Mars colony?"

    res = service.ask(query=query)
    assert "do not contain sufficient evidence" in res.answer.lower() or "not contain sufficient" in res.answer.lower()
    assert len(res.sources) == 0
