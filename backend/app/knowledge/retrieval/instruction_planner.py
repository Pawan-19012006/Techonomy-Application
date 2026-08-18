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
    normalized_question: str = Field(default="", description="Normalized user question")
    question_archetype: str = Field(default="ANALYTICAL", description="SIMPLE_FACTUAL | ANALYTICAL | COMPARATIVE | STRATEGIC_DIAGNOSTIC")
    response_depth_target: str = Field(default="DETAILED_ANALYSIS", description="Target response depth profile")
    adaptive_token_budget: int = Field(default=3500, description="Dynamic token ceiling for ContextBuilder")
    target_top_n: int = Field(default=8, description="Target top N reranked chunks")
    entities: List[str] = Field(default_factory=list, description="Extracted company or product entities")
    required_metrics: List[str] = Field(default_factory=list, description="Metrics or evidence fields required")
    concepts: List[str] = Field(default_factory=list, description="Expanded analytical concepts and terms")
    preferred_document_types: List[str] = Field(default_factory=list, description="Preferred document types")
    temporal_reference: Optional[str] = Field(default=None, description="Extracted temporal reference")
    resolved_periods: List[str] = Field(default_factory=list, description="Resolved reporting periods")
    comparison_type: Optional[str] = Field(default=None, description="Comparison type (yoy, mom, multi_year)")
    analytical_operations: List[str] = Field(default_factory=list, description="Target analytical/mathematical operations")
    calculation_requirements: List[str] = Field(default_factory=list, description="Calculations required (growth %, margin, sum)")
    cross_domain_requirements: List[str] = Field(default_factory=list, description="Multiple evidence domains required")
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

        # Lazy load resolvers
        from app.knowledge.retrieval.temporal_resolver import TemporalResolver
        from app.knowledge.retrieval.concept_expander import ConceptExpander
        self.temporal_resolver = TemporalResolver()
        self.concept_expander = ConceptExpander()

    def retrieve_instruction_guidance(
        self,
        query: str,
        top_k: int = 4,
    ) -> List[SearchResult]:
        """Queries the internal instruction_knowledge collection for analytical guidance."""
        try:
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
        """Constructs a RetrievalPlan combining temporal resolution, instruction concepts, and domain heuristics."""
        normalized_q = query.lower().strip()

        # 1. Temporal Resolution
        temp_res = self.temporal_resolver.resolve(query)

        # 2. Extract Instruction Terms
        inst_terms: List[str] = []
        guidance_summaries: List[str] = []
        for idx, chunk in enumerate(instruction_chunks, start=1):
            guidance_summaries.append(f"[Guidance {idx}]: {chunk.content[:200].strip()}")
            matches = re.findall(r"\b(?:revenue|gross profit|operating income|EBITDA|net profit|COGS|on-time delivery|quality score|defect rate|sales volume|inventory days|receivable days|working capital)\b", chunk.content, re.IGNORECASE)
            if matches:
                inst_terms.extend([m.lower() for m in matches])

        # 3. Concept & Synonym Expansion
        concept_exp = self.concept_expander.expand(query, instruction_terms=inst_terms)

        # 4. Domain Intent Detection & Archetype Classification
        intent = "general_analytical_inquiry"
        required_metrics: List[str] = []
        preferred_doc_types: List[str] = []
        operations: List[str] = []
        calculation_reqs: List[str] = []
        cross_domain_reqs: List[str] = []

        # Question Archetype Classification
        if any(w in normalized_q for w in ["risk assessment", "risks", "achieve", "bottlenecks", "strategic assessment", "overall performance"]):
            archetype = "STRATEGIC_DIAGNOSTIC"
            depth_target = "MULTI_SECTION_DEEP_DIVE"
            token_budget = 4500
            top_n_val = 10
        elif any(w in normalized_q for w in ["compare", "changed", "across", "trend", "yoy", "year over year", "growth rate", "period"]):
            archetype = "COMPARATIVE"
            depth_target = "STRUCTURED_COMPARISON"
            token_budget = 4000
            top_n_val = 10
        elif any(w in normalized_q for w in ["concern", "concerns", "working capital", "profitability", "issues", "why", "how", "performance", "factors", "drivers", "review"]):
            archetype = "ANALYTICAL"
            depth_target = "DETAILED_ANALYSIS"
            token_budget = 3500
            top_n_val = 8
        elif len(normalized_q.split()) <= 6 and not any(w in normalized_q for w in ["why", "how", "concern", "changed", "compare"]):
            archetype = "SIMPLE_FACTUAL"
            depth_target = "CONCISE"
            token_budget = 2000
            top_n_val = 5
        else:
            archetype = "ANALYTICAL"
            depth_target = "DETAILED_ANALYSIS"
            token_budget = 3500
            top_n_val = 8

        if any(w in normalized_q for w in ["revenue", "profit", "ebitda", "margin", "expense", "financial", "growth", "cost", "performance", "period", "earnings", "balance", "working capital", "profitability"]):
            intent = "financial_analysis"
            preferred_doc_types.extend(["financial_statement", "annual_report", "balance_sheet", "income_statement"])
            required_metrics.extend(["revenue", "gross_profit", "operating_income", "ebitda", "net_profit", "operating_expenses"])
            operations.extend(["growth_percentage_calculation", "year_over_year_period_comparison", "margin_analysis"])
            calculation_reqs.extend(["yoy_growth_percentage", "net_profit_margin", "absolute_change"])

            if any(w in normalized_q for w in ["why", "reason", "despite", "drove", "impact"]):
                cross_domain_reqs.append("financial_cost_operations_correlation")

        if any(w in normalized_q for w in ["vendor", "supplier", "delivery", "quality", "contract", "compliance", "score", "procurement"]):
            if intent == "general_analytical_inquiry":
                intent = "vendor_evaluation"
            preferred_doc_types.extend(["vendor_evaluation_report", "procurement_scorecard", "supplier_audit"])
            required_metrics.extend(["quality_score", "delivery_performance", "pricing_competitiveness", "on_time_delivery"])
            operations.extend(["vendor_scorecard_evaluation", "sla_compliance_check"])

        if any(w in normalized_q for w in ["sales", "unit", "customer", "region", "segment", "product", "cohort", "month", "transaction"]):
            if intent == "general_analytical_inquiry":
                intent = "sales_performance"
            preferred_doc_types.extend(["sales_report", "market_analysis", "cohort_report", "transaction_analytics"])
            required_metrics.extend(["sales_volume", "regional_revenue", "product_performance", "cohort_retention"])
            operations.extend(["regional_distribution_analysis", "cohort_growth_comparison"])

        if any(w in normalized_q for w in ["marketing", "campaign", "ad", "channel", "cac", "roas"]):
            preferred_doc_types.extend(["marketing_campaign_report", "customer_analytics"])
            required_metrics.extend(["marketing_expenditure", "campaign_roi", "acquisition_cost"])
            cross_domain_reqs.append("marketing_sales_attribution")

        if any(w in normalized_q for w in ["working capital", "inventory", "receivable", "payable", "cash"]):
            required_metrics.extend(["inventory_days", "receivable_days", "payable_days", "working_capital_cycle"])
            preferred_doc_types.extend(["finance_commercial_economics", "working_capital_report"])

        # 5. Assemble Multi-Query Search Batch
        company_queries: List[str] = [query]
        company_queries.extend(temp_res.temporal_search_terms)
        company_queries.extend(concept_exp.generated_subqueries)

        if temp_res.resolved_periods:
            company_queries.append(" ".join(temp_res.resolved_periods) + " revenue net profit financial performance")

        # Deduplicate company search queries
        unique_queries = list(dict.fromkeys([q for q in company_queries if q.strip()]))

        summary_text = "\n".join(guidance_summaries) if guidance_summaries else "Standard analytical query decomposition applied."

        plan = RetrievalPlan(
            intent=intent,
            normalized_question=normalized_q,
            question_archetype=archetype,
            response_depth_target=depth_target,
            adaptive_token_budget=token_budget,
            target_top_n=top_n_val,
            required_metrics=list(dict.fromkeys(required_metrics)),
            concepts=concept_exp.primary_concepts + concept_exp.expanded_terms[:10],
            preferred_document_types=list(dict.fromkeys(preferred_doc_types)),
            temporal_reference=temp_res.original_reference,
            resolved_periods=temp_res.resolved_periods,
            comparison_type=temp_res.comparison_type,
            analytical_operations=list(dict.fromkeys(operations)),
            calculation_requirements=list(dict.fromkeys(calculation_reqs)),
            cross_domain_requirements=list(dict.fromkeys(cross_domain_reqs)),
            company_search_queries=unique_queries,
            instruction_guidance_summary=summary_text,
            instruction_chunks_retrieved=len(instruction_chunks),
        )

        logger.info(f"[RETRIEVAL PLAN GENERATED] archetype='{plan.question_archetype}' | intent='{plan.intent}' | budget={plan.adaptive_token_budget} | queries={len(plan.company_search_queries)}")
        return plan
