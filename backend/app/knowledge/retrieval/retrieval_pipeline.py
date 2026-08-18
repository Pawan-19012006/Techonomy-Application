"""Retrieval Pipeline coordinator orchestrating Phase 5 Knowledge Retrieval Engine with deterministic Query Decomposition."""

import time
from typing import Any, Dict, List, Optional
from app.config import settings
from app.knowledge.exceptions import RetrievalPipelineError
from app.knowledge.models.retrieval_result import RetrievalResult
from app.knowledge.retrieval.context_builder import ContextBuilder
from app.knowledge.retrieval.query_decomposer import QueryDecomposer
from app.knowledge.retrieval.query_embedder import QueryEmbedder
from app.knowledge.retrieval.query_processor import QueryProcessor
from app.knowledge.retrieval.reranker import Reranker
from app.knowledge.retrieval.search_filters import SearchFilters
from app.knowledge.retrieval.vector_search import VectorSearch
from app.knowledge.retrieval.instruction_planner import InstructionPlanner
from app.utils.logging import logger
from app.utils.observability import (
    get_request_id,
    log_structured_event,
    sanitize_error_message,
)


class RetrievalPipeline:
    """Orchestrates Phase 5 Two-Stage Knowledge Retrieval pipeline:
    Stage 1 (Instruction RAG & Retrieval Plan) -> Stage 2 (Company Vector Search & Evidence Validation) -> Rerank -> ContextBuilder.
    """

    def __init__(
        self,
        query_processor: Optional[QueryProcessor] = None,
        query_embedder: Optional[QueryEmbedder] = None,
        vector_search: Optional[VectorSearch] = None,
        reranker: Optional[Reranker] = None,
        context_builder: Optional[ContextBuilder] = None,
        query_decomposer: Optional[QueryDecomposer] = None,
        instruction_planner: Optional[InstructionPlanner] = None,
    ):
        """Initializes RetrievalPipeline with injected module components."""
        self.query_processor = query_processor or QueryProcessor()
        self.query_embedder = query_embedder or QueryEmbedder()
        self.vector_search = vector_search or VectorSearch()
        self.reranker = reranker or Reranker()
        self.context_builder = context_builder or ContextBuilder()
        self.query_decomposer = query_decomposer or QueryDecomposer()
        self.instruction_planner = instruction_planner or InstructionPlanner()

    def retrieve(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        top_k: int = settings.RETRIEVAL_TOP_K,
        top_n: int = settings.RETRIEVAL_RERANK_TOP_N,
        token_budget: int = settings.RETRIEVAL_CONTEXT_TOKEN_BUDGET,
        request_id: Optional[str] = None,
        tracker: Optional[Any] = None,
    ) -> RetrievalResult:
        """Executes full Knowledge Retrieval Engine pipeline supporting two-stage instruction-guided retrieval."""
        pipeline_start = time.perf_counter()
        req_id = get_request_id(request_id)
        logger.info(f"=== Starting Two-Stage Knowledge Retrieval Engine (req_id={req_id}) for query: '{query[:60]}...' ===")

        try:
            # STAGE 1: Instruction RAG & Retrieval Plan Generation
            t_inst0 = time.perf_counter()
            instruction_chunks = self.instruction_planner.retrieve_instruction_guidance(query=query)
            retrieval_plan = self.instruction_planner.create_retrieval_plan(query=query, instruction_chunks=instruction_chunks)
            t_instruction_ms = (time.perf_counter() - t_inst0) * 1000.0

            # Query Processor & Query Decomposition
            t0 = time.perf_counter()
            processed_query = self.query_processor.process(query)
            decomposed_subqueries = self.query_decomposer.decompose(processed_query.normalized_query)

            # Merge decomposed subqueries with instruction plan search queries
            combined_queries = list(dict.fromkeys(decomposed_subqueries + retrieval_plan.company_search_queries))
            subquery_count = len(combined_queries)

            subquery_log = [
                f"\n[TWO-STAGE QUERY PLAN]\nintent={retrieval_plan.intent}\noriginal={processed_query.normalized_query}\nquery_count={subquery_count}"
            ]
            for idx, sq in enumerate(combined_queries, start=1):
                subquery_log.append(f"query_{idx}={sq}")
            logger.info("\n".join(subquery_log))

            t_qp = time.perf_counter() - t0

            # STAGE 2: Company Evidence Retrieval (company_knowledge ONLY)
            t_embed_total = 0.0
            t_search_total = 0.0
            merged_raw_matches = []
            seen_keys = set()
            dimension = 384

            # Enforce Strict Company Evidence Boundary Filter
            company_filters = filters if filters is not None else SearchFilters()
            company_filters.document_type = "company"
            company_filters.visibility = "user_visible"

            doc_chunk_counts = {}
            for sq in combined_queries:
                sq_processed = self.query_processor.process(sq)

                t1 = time.perf_counter()
                sq_vector = self.query_embedder.embed_query(sq_processed)
                dimension = self.query_embedder.get_dimension()
                t_embed_total += time.perf_counter() - t1

                t2 = time.perf_counter()
                sq_matches = self.vector_search.search(
                    query_vector=sq_vector,
                    top_k=top_k,
                    filters=company_filters,
                    collection_name=settings.QDRANT_COMPANY_COLLECTION_NAME,
                )
                t_search_total += time.perf_counter() - t2

                # Deduplicate candidates across queries and enforce company boundary & document diversification
                for match in sq_matches:
                    doc_type = getattr(match, "document_type", "company")
                    vis = getattr(match, "visibility", "user_visible")
                    # Strict Evidence Gate: Never allow instruction chunks into company evidence
                    if doc_type == "instruction" or vis == "internal":
                        continue

                    # Document Diversification Cap: Prevent a single document from monopolizing candidates
                    dname = match.document_name
                    if doc_chunk_counts.get(dname, 0) >= 3:
                        continue

                    pages_tuple = tuple(sorted(match.page_numbers)) if match.page_numbers else ()
                    unique_key = (match.document_name, pages_tuple, match.chunk_id)
                    if unique_key not in seen_keys:
                        seen_keys.add(unique_key)
                        doc_chunk_counts[dname] = doc_chunk_counts.get(dname, 0) + 1
                        merged_raw_matches.append(match)

            # STAGE 2.5: Evidence Coverage Assessment & Iterative Second-Pass Retrieval
            from app.knowledge.retrieval.evidence_checker import EvidenceChecker
            evidence_checker = EvidenceChecker()
            coverage_report = evidence_checker.check_coverage(
                candidates=merged_raw_matches,
                required_metrics=retrieval_plan.required_metrics,
                intent=retrieval_plan.intent,
            )

            if not coverage_report.is_sufficient and coverage_report.targeted_fallback_queries:
                logger.info(f"[ITERATIVE RETRIEVAL] Coverage incomplete (Missing: {coverage_report.missing_metrics}). Executing {len(coverage_report.targeted_fallback_queries)} targeted fallback queries...")
                for fb_sq in coverage_report.targeted_fallback_queries:
                    fb_proc = self.query_processor.process(fb_sq)
                    fb_vec = self.query_embedder.embed_query(fb_proc)
                    fb_hits = self.vector_search.search(
                        query_vector=fb_vec,
                        top_k=top_k,
                        filters=company_filters,
                        collection_name=settings.QDRANT_COMPANY_COLLECTION_NAME,
                    )
                    for match in fb_hits:
                        doc_type = getattr(match, "document_type", "company")
                        vis = getattr(match, "visibility", "user_visible")
                        if doc_type == "instruction" or vis == "internal":
                            continue

                        pages_tuple = tuple(sorted(match.page_numbers)) if match.page_numbers else ()
                        unique_key = (match.document_name, pages_tuple, match.chunk_id)
                        if unique_key not in seen_keys:
                            seen_keys.add(unique_key)
                            merged_raw_matches.append(match)

            embed_ms = t_embed_total * 1000.0
            qdrant_ms = t_search_total * 1000.0
            chunk_cnt = len(merged_raw_matches)

            log_structured_event("EMBEDDING_COMPLETE", req_id, duration_ms=embed_ms)
            log_structured_event(
                "QDRANT_RETRIEVAL_COMPLETE",
                req_id,
                duration_ms=qdrant_ms,
                chunks=chunk_cnt,
                succeeded=True,
                zero_results=(chunk_cnt == 0),
            )

            if tracker and hasattr(tracker, "record_embedding"):
                try:
                    tracker.record_embedding(embed_ms)
                    tracker.record_qdrant(
                        duration_ms=qdrant_ms,
                        chunk_count=chunk_cnt,
                        succeeded=True,
                        zero_results=(chunk_cnt == 0),
                    )
                except Exception as t_err:
                    logger.warning(f"Tracker record failed in retrieve: {t_err}")

            # Stage 4: Adaptive Reranker on Merged Candidates
            t3 = time.perf_counter()
            effective_top_n = max(top_n, getattr(retrieval_plan, "target_top_n", top_n))
            reranked_matches = self.reranker.rerank(
                results=merged_raw_matches,
                query=processed_query,
                top_n=effective_top_n,
            )
            t_rerank = time.perf_counter() - t3

            # Stage 5: Context Builder with Adaptive Token Ceiling
            t4 = time.perf_counter()
            effective_budget = token_budget if token_budget is not None else getattr(retrieval_plan, "adaptive_token_budget", settings.RETRIEVAL_CONTEXT_TOKEN_BUDGET)
            context_package = self.context_builder.build_context(
                reranked_results=reranked_matches,
                token_budget=effective_budget,
            )
            t_context = time.perf_counter() - t4

            total_elapsed = time.perf_counter() - pipeline_start

            timing: Dict[str, float] = {
                "query_processing": round(t_qp, 4),
                "embedding": round(t_embed_total, 4),
                "vector_search": round(t_search_total, 4),
                "reranking": round(t_rerank, 4),
                "context_building": round(t_context, 4),
                "retrieval_total": round(total_elapsed, 4),
            }

            result = RetrievalResult(
                processed_query=processed_query,
                embedding_dimension=dimension,
                top_k_searched=len(merged_raw_matches),
                top_n_reranked=len(reranked_matches),
                raw_search_results=merged_raw_matches,
                reranked_results=reranked_matches,
                context_package=context_package,
                processing_time=round(total_elapsed, 3),
                timing=timing,
                retrieval_plan=retrieval_plan,
            )

            logger.info(
                f"=== Completed Knowledge Retrieval Engine (req_id={req_id}) === "
                f"[QP: {t_qp:.3f}s, Embed: {t_embed_total:.3f}s, Search: {t_search_total:.3f}s, "
                f"Rerank: {t_rerank:.3f}s, Context: {t_context:.3f}s, Total: {total_elapsed:.3f}s]"
            )
            return result

        except Exception as e:
            elapsed_ms = (time.perf_counter() - pipeline_start) * 1000.0
            log_structured_event(
                "STAGE_FAILURE",
                req_id,
                stage="retrieval",
                duration_ms=elapsed_ms,
                error_type=type(e).__name__,
            )
            logger.error(f"Retrieval Pipeline execution failed for query (req_id={req_id}): {sanitize_error_message(e)}")
            raise RetrievalPipelineError(f"Retrieval pipeline failed: {sanitize_error_message(e)}") from e


def retrieve_context(
    query: str,
    filters: Optional[SearchFilters] = None,
    top_k: int = settings.RETRIEVAL_TOP_K,
    top_n: int = settings.RETRIEVAL_RERANK_TOP_N,
) -> RetrievalResult:
    """Helper function to execute Phase 5 Knowledge Retrieval Engine pipeline."""
    pipeline = RetrievalPipeline()
    return pipeline.retrieve(query=query, filters=filters, top_k=top_k, top_n=top_n)
