"""Instruction Planner coordinating Stage 1 (Instruction Knowledge Retrieval) & Retrieval Plan Generation."""

import re
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from app.config import settings
from app.knowledge.models.search_result import SearchResult
from app.knowledge.retrieval.query_embedder import QueryEmbedder
from app.knowledge.retrieval.search_filters import SearchFilters
from app.knowledge.retrieval.vector_search import VectorSearch
from app.utils.logging import logger


class RetrievalPlan(BaseModel):
    """Domain model representing the output of Stage 1 Instruction Planning."""

    intent: str = Field(default="general_inquiry", description="Detected query analytical intent")
    required_metrics: List[str] = Field(default_factory=list, description="Metrics or evidence fields required")
    preferred_document_types: List[str] = Field(default_factory=list, description="Preferred document types")
    analytical_operations: List[str] = Field(default_factory=list, description="Target analytical/mathematical operations")
    company_search_queries: List[str] = Field(default_factory=list, description="Search queries for company documents")
    instruction_guidance_summary: str = Field(default="", description="Internal guidance summary derived from instruction dataset")
    instruction_chunks_retrieved: int = Field(default=0, description="Number of instruction chunks retrieved")


class InstructionPlanner:
    """Orchestrates Stage 1 Instruction Knowledge Retrieval and builds structured RetrievalPlans."""

    def __init__(
        self,
        vector_search: Optional[VectorSearch] = None,
        query_embedder: Optional[QueryEmbedder] = None,
        instruction_collection_name: str = settings.QDRANT_INSTRUCTION_COLLECTION_NAME,
    ):
        self.vector_search = vector_search or VectorSearch()
        self.query_embedder = query_embedder or QueryEmbedder()
        self.instruction_collection_name = instruction_collection_name

    def retrieve_instruction_guidance(
        self,
        query: str,
        top_k: int = 4,
    ) -> List[SearchResult]:
        """Queries the internal instruction_knowledge collection for analytical guidance.

        Args:
            query (str): User query text.
            top_k (int): Number of instruction guidance chunks to retrieve.

        Returns:
            List[SearchResult]: Retrieved instruction guidance chunks (visibility = 'internal').
        """
        try:
            # Embed query
            class DummyProcessedQuery:
                def __init__(self, q: str):
                    self.normalized_query = q

            query_vector = self.query_embedder.embed_query(DummyProcessedQuery(query))

            # Filter for internal instruction knowledge
            filters = SearchFilters(document_type="instruction", visibility="internal", minimum_similarity=0.15)

            results = self.vector_search.search(
                query_vector=query_vector,
                top_k=top_k,
                filters=filters,
                collection_name=self.instruction_collection_name,
            )
            logger.info(f"[STAGE 1 INSTRUCTION RAG] Retrieved {len(results)} instruction guidance chunks from '{self.instruction_collection_name}'")
            return results
        except Exception as e:
            logger.warning(f"[STAGE 1 INSTRUCTION RAG NOTICE] Instruction collection search unavailable: {e}. Falling back to heuristic planner.")
            return []

    def create_retrieval_plan(
        self,
        query: str,
        instruction_chunks: List[SearchResult],
    ) -> RetrievalPlan:
        """Constructs a RetrievalPlan combining retrieved instruction guidance and query domain heuristics."""
        normalized_q = query.lower()

        intent = "general_inquiry"
        required_metrics: List[str] = []
        preferred_doc_types: List[str] = []
        operations: List[str] = []
        company_queries: List[str] = [query]

        # Domain intent detection
        if any(w in normalized_q for w in ["revenue", "profit", "ebitda", "margin", "expense", "financial", "growth", "cost"]):
            intent = "financial_analysis"
            preferred_doc_types.extend(["financial_statement", "annual_report", "balance_sheet"])
            
            if "revenue" in normalized_q:
                required_metrics.append("revenue")
                company_queries.extend(["annual revenue total sales", "revenue growth comparison"])
            if "profit" in normalized_q or "ebitda" in normalized_q or "margin" in normalized_q:
                required_metrics.extend(["gross_profit", "net_profit", "operating_margin"])
                company_queries.extend(["gross net profit margin", "EBITDA operating income"])
            if "growth" in normalized_q or "year" in normalized_q or "yoy" in normalized_q or "compared" in normalized_q:
                operations.append("growth_percentage_calculation")
                operations.append("year_over_year_period_comparison")

        elif any(w in normalized_q for w in ["vendor", "supplier", "delivery", "quality", "contract", "compliance", "score"]):
            intent = "vendor_evaluation"
            preferred_doc_types.extend(["vendor_evaluation_report", "procurement_scorecard"])
            required_metrics.extend(["quality_score", "delivery_performance", "pricing_competitiveness"])
            company_queries.extend(["vendor performance evaluation score", "delivery quality contract compliance"])

        elif any(w in normalized_q for w in ["sales", "unit", "customer", "region", "segment", "product"]):
            intent = "sales_performance"
            preferred_doc_types.extend(["sales_report", "market_analysis"])
            required_metrics.extend(["sales_volume", "regional_revenue", "product_performance"])
            company_queries.extend(["sales volume product performance", "regional sales customer segment"])

        # Extract guidance summary from instruction chunks if retrieved
        guidance_summaries = []
        for idx, chunk in enumerate(instruction_chunks, start=1):
            guidance_summaries.append(f"[Guidance {idx}]: {chunk.content[:200].strip()}")

        summary_text = "\n".join(guidance_summaries) if guidance_summaries else "Standard analytical query decomposition applied."

        # Deduplicate company search queries
        unique_queries = list(dict.fromkeys([q for q in company_queries if q.strip()]))

        plan = RetrievalPlan(
            intent=intent,
            required_metrics=required_metrics,
            preferred_document_types=preferred_doc_types,
            analytical_operations=operations,
            company_search_queries=unique_queries,
            instruction_guidance_summary=summary_text,
            instruction_chunks_retrieved=len(instruction_chunks),
        )

        logger.info(f"[RETRIEVAL PLAN GENERATED] intent='{plan.intent}' | queries={plan.company_search_queries} | operations={plan.analytical_operations}")
        return plan
