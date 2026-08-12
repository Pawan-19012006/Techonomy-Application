"""Retrieval Pipeline coordinator orchestrating Phase 5 Knowledge Retrieval Engine."""

import time
from typing import Dict, Optional
from app.config import settings
from app.knowledge.exceptions import RetrievalPipelineError
from app.knowledge.models.retrieval_result import RetrievalResult
from app.knowledge.retrieval.context_builder import ContextBuilder
from app.knowledge.retrieval.query_embedder import QueryEmbedder
from app.knowledge.retrieval.query_processor import QueryProcessor
from app.knowledge.retrieval.reranker import Reranker
from app.knowledge.retrieval.search_filters import SearchFilters
from app.knowledge.retrieval.vector_search import VectorSearch
from app.utils.logging import logger


class RetrievalPipeline:
    """Orchestrates Phase 5 Knowledge Retrieval pipeline: Query -> Normalize -> Embed -> VectorSearch -> Rerank -> ContextBuilder -> RetrievalResult."""

    def __init__(
        self,
        query_processor: Optional[QueryProcessor] = None,
        query_embedder: Optional[QueryEmbedder] = None,
        vector_search: Optional[VectorSearch] = None,
        reranker: Optional[Reranker] = None,
        context_builder: Optional[ContextBuilder] = None,
    ):
        """Initializes RetrievalPipeline with injected module components."""
        self.query_processor = query_processor or QueryProcessor()
        self.query_embedder = query_embedder or QueryEmbedder()
        self.vector_search = vector_search or VectorSearch()
        self.reranker = reranker or Reranker()
        self.context_builder = context_builder or ContextBuilder()

    def retrieve(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        top_k: int = settings.RETRIEVAL_TOP_K,
        top_n: int = settings.RETRIEVAL_RERANK_TOP_N,
        token_budget: int = settings.RETRIEVAL_CONTEXT_TOKEN_BUDGET,
    ) -> RetrievalResult:
        """Executes full Knowledge Retrieval Engine pipeline for a user question with high-resolution timing."""
        pipeline_start = time.perf_counter()
        logger.info(f"=== Starting Knowledge Retrieval Engine for query: '{query[:60]}...' ===")

        try:
            # Stage 1: Query Processor
            t0 = time.perf_counter()
            processed_query = self.query_processor.process(query)
            t_qp = time.perf_counter() - t0

            # Stage 2: Query Embedder
            t1 = time.perf_counter()
            query_vector = self.query_embedder.embed_query(processed_query)
            dimension = self.query_embedder.get_dimension()
            t_embed = time.perf_counter() - t1

            # Stage 3: Vector Search
            t2 = time.perf_counter()
            raw_matches = self.vector_search.search(
                query_vector=query_vector,
                top_k=top_k,
                filters=filters,
            )
            t_search = time.perf_counter() - t2

            # Stage 4: Reranker
            t3 = time.perf_counter()
            reranked_matches = self.reranker.rerank(
                results=raw_matches,
                query=processed_query,
                top_n=top_n,
            )
            t_rerank = time.perf_counter() - t3

            # Stage 5: Context Builder
            t4 = time.perf_counter()
            context_package = self.context_builder.build_context(
                reranked_results=reranked_matches,
                token_budget=token_budget,
            )
            t_context = time.perf_counter() - t4

            total_elapsed = time.perf_counter() - pipeline_start

            timing: Dict[str, float] = {
                "query_processing": round(t_qp, 4),
                "embedding": round(t_embed, 4),
                "vector_search": round(t_search, 4),
                "reranking": round(t_rerank, 4),
                "context_building": round(t_context, 4),
                "retrieval_total": round(total_elapsed, 4),
            }

            result = RetrievalResult(
                processed_query=processed_query,
                embedding_dimension=dimension,
                top_k_searched=len(raw_matches),
                top_n_reranked=len(reranked_matches),
                raw_search_results=raw_matches,
                reranked_results=reranked_matches,
                context_package=context_package,
                processing_time=round(total_elapsed, 3),
                timing=timing,
            )

            logger.info(
                f"=== Completed Knowledge Retrieval Engine === "
                f"[QP: {t_qp:.3f}s, Embed: {t_embed:.3f}s, Search: {t_search:.3f}s, "
                f"Rerank: {t_rerank:.3f}s, Context: {t_context:.3f}s, Total: {total_elapsed:.3f}s]"
            )
            return result

        except Exception as e:
            logger.error(f"Retrieval Pipeline execution failed for query '{query}': {e}")
            raise RetrievalPipelineError(f"Retrieval pipeline failed: {str(e)}") from e


def retrieve_context(
    query: str,
    filters: Optional[SearchFilters] = None,
    top_k: int = settings.RETRIEVAL_TOP_K,
    top_n: int = settings.RETRIEVAL_RERANK_TOP_N,
) -> RetrievalResult:
    """Helper function to execute Phase 5 Knowledge Retrieval Engine pipeline."""
    pipeline = RetrievalPipeline()
    return pipeline.retrieve(query=query, filters=filters, top_k=top_k, top_n=top_n)
