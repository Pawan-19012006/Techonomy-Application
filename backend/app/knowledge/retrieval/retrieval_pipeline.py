"""Retrieval Pipeline coordinator orchestrating Phase 5 Knowledge Retrieval Engine."""

import time
from typing import Optional
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
        """Executes full Knowledge Retrieval Engine pipeline for a user question.

        Pipeline Steps:
            1. Query Processor -> Normalize and validate question text.
            2. Query Embedder -> Generate L2-normalized dense vector embedding.
            3. Vector Search -> Query Qdrant vector collection for top_k similarity matches.
            4. Reranker -> Apply hybrid semantic + heuristic keyword reranking for top_n matches.
            5. Context Builder -> Synthesize deduplicated ContextPackage respecting token_budget.

        Args:
            query (str): Raw user question string.
            filters (Optional[SearchFilters]): Reusable search filters.
            top_k (int): Number of initial vector matches to retrieve (default 10).
            top_n (int): Number of top reranked matches to select (default 5).
            token_budget (int): Token budget ceiling for context (default 2000).

        Returns:
            RetrievalResult: Complete retrieval outcome domain model.

        Raises:
            RetrievalPipelineError: If retrieval pipeline fails.
        """
        start_time = time.time()
        logger.info(f"=== Starting Knowledge Retrieval Engine for query: '{query[:60]}...' ===")

        try:
            # Step 1: Query Processor
            processed_query = self.query_processor.process(query)

            # Step 2: Query Embedder
            query_vector = self.query_embedder.embed_query(processed_query)
            dimension = self.query_embedder.get_dimension()

            # Step 3: Vector Search
            raw_matches = self.vector_search.search(
                query_vector=query_vector,
                top_k=top_k,
                filters=filters,
            )

            # Step 4: Reranker
            reranked_matches = self.reranker.rerank(
                results=raw_matches,
                query=processed_query,
                top_n=top_n,
            )

            # Step 5: Context Builder
            context_package = self.context_builder.build_context(
                reranked_results=reranked_matches,
                token_budget=token_budget,
            )

            elapsed = time.time() - start_time

            result = RetrievalResult(
                processed_query=processed_query,
                embedding_dimension=dimension,
                top_k_searched=len(raw_matches),
                top_n_reranked=len(reranked_matches),
                raw_search_results=raw_matches,
                reranked_results=reranked_matches,
                context_package=context_package,
                processing_time=round(elapsed, 3),
            )

            logger.info(
                f"=== Completed Knowledge Retrieval Engine === "
                f"[Query: '{processed_query.normalized_query[:30]}...', Hits: {len(raw_matches)}, "
                f"Reranked: {len(reranked_matches)}, Context Tokens: {context_package.estimated_tokens}, "
                f"Time: {result.processing_time}s]"
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
