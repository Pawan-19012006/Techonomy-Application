"""Comprehensive test suite verifying dataset isolation, two-stage instruction RAG, hard evidence boundary, citation security, and independent resets."""

import pytest
from app.config import settings
from app.knowledge.ingestion.ingest import (
    reset_company_knowledge,
    reset_instruction_knowledge,
)
from app.knowledge.models.search_result import SearchResult
from app.knowledge.rag.chat_service import ChatService
from app.knowledge.rag.prompt_builder import PromptBuilder
from app.knowledge.retrieval.instruction_planner import InstructionPlanner, RetrievalPlan
from app.knowledge.retrieval.retrieval_pipeline import RetrievalPipeline
from app.schemas.chat import SourceItem


def test_1_collection_isolation():
    """Test 1: Verify company_knowledge and instruction_knowledge collections are configured separately."""
    assert settings.QDRANT_COMPANY_COLLECTION_NAME == "company_knowledge"
    assert settings.QDRANT_INSTRUCTION_COLLECTION_NAME == "instruction_knowledge"
    assert settings.QDRANT_COMPANY_COLLECTION_NAME != settings.QDRANT_INSTRUCTION_COLLECTION_NAME


def test_2_two_stage_retrieval_and_plan():
    """Test 2: Stage 1 instruction retrieval produces a structured RetrievalPlan."""
    planner = InstructionPlanner()
    
    # Simulate query
    query = "What was the company's revenue growth last year?"
    guidance_chunks = planner.retrieve_instruction_guidance(query=query)
    
    # Create plan
    plan = planner.create_retrieval_plan(query=query, instruction_chunks=guidance_chunks)
    
    assert isinstance(plan, RetrievalPlan)
    assert plan.intent == "financial_analysis"
    assert "revenue" in plan.required_metrics
    assert len(plan.company_search_queries) > 0
    assert any("revenue" in q.lower() for q in plan.company_search_queries)


def test_3_hard_evidence_boundary():
    """Test 3: Verify RetrievalPipeline filters out instruction chunks from company evidence context."""
    pipeline = RetrievalPipeline()
    result = pipeline.retrieve("What was revenue growth last year?")
    
    assert hasattr(result, "reranked_results")
    assert hasattr(result, "retrieval_plan")
    assert isinstance(result.retrieval_plan, RetrievalPlan)
    
    # Assert every reranked chunk is strictly a company document
    for chunk in result.reranked_results:
        doc_type = getattr(chunk, "document_type", "company")
        visibility = getattr(chunk, "visibility", "user_visible")
        assert doc_type == "company", f"Instruction document '{chunk.document_name}' leaked into company evidence!"
        assert visibility == "user_visible", f"Internal document '{chunk.document_name}' leaked into user visible evidence!"


def test_4_sources_contain_only_company_documents():
    """Test 4: Verify ChatService._extract_sources strictly excludes instruction documents from participant citations."""
    chat_service = ChatService()
    
    # Create mock retrieval result containing mixed chunks
    company_chunk = SearchResult(
        document_id="doc-company-1",
        document_name="Financial Statement 2025.pdf",
        chunk_id="chk-1",
        content="Revenue in 2025 reached $120 million.",
        page_numbers=[35],
        score=0.92,
        metadata={"document_type": "company", "visibility": "user_visible"},
    )
    # Add attributes directly to simulate Qdrant payload
    company_chunk.document_type = "company"
    company_chunk.visibility = "user_visible"

    instruction_chunk = SearchResult(
        document_id="doc-inst-1",
        document_name="financial_analysis_instruction.pdf",
        chunk_id="chk-2",
        content="To compute YoY revenue growth use ((Current - Prior) / Prior) * 100",
        page_numbers=[1],
        score=0.88,
        metadata={"document_type": "instruction", "visibility": "internal"},
    )
    instruction_chunk.document_type = "instruction"
    instruction_chunk.visibility = "internal"

    class MockRetrievalResult:
        reranked_results = [company_chunk, instruction_chunk]

    sources = chat_service._extract_sources(MockRetrievalResult())
    
    # Verify ONLY company document appears in extracted citations
    assert len(sources) == 1
    assert sources[0].document == "Financial Statement 2025.pdf"
    assert sources[0].page == 35
    assert not any(s.document == "financial_analysis_instruction.pdf" for s in sources)


def test_5_prompt_builder_company_evidence_isolation():
    """Test 5: PromptBuilder format_context_chunks excludes instruction documents from prompt context."""
    prompt_builder = PromptBuilder()

    company_chunk = SearchResult(
        document_id="doc-c1",
        document_name="Annual Report.pdf",
        chunk_id="c1",
        content="Net profit grew 15% year over year.",
        page_numbers=[12],
        score=0.9,
    )
    company_chunk.document_type = "company"
    company_chunk.visibility = "user_visible"

    instruction_chunk = SearchResult(
        document_id="doc-i1",
        document_name="vendor_evaluation_instruction.pdf",
        chunk_id="i1",
        content="Instruction content: evaluate vendor delivery score.",
        page_numbers=[1],
        score=0.85,
    )
    instruction_chunk.document_type = "instruction"
    instruction_chunk.visibility = "internal"

    formatted_context = prompt_builder.format_context_chunks([company_chunk, instruction_chunk])

    assert "Annual Report.pdf" in formatted_context
    assert "vendor_evaluation_instruction.pdf" not in formatted_context
    assert "Instruction content" not in formatted_context


def test_6_independent_resets():
    """Test 6: Verify independent reset functions recreate specific collections without error."""
    success_comp = reset_company_knowledge()
    assert success_comp is True

    success_inst = reset_instruction_knowledge()
    assert success_inst is True
