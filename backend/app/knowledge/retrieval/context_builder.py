"""Context Builder for synthesizing curated, deduplicated, and budget-constrained context packages."""

from typing import List, Optional, Set
from app.config import settings
from app.knowledge.exceptions import ContextBuilderError
from app.knowledge.models.context_package import ContextPackage
from app.knowledge.models.search_result import SearchResult
from app.knowledge.optimization.token_estimator import TokenEstimator
from app.utils.logging import logger


class ContextBuilder:
    """Synthesizes reranked SearchResult matches into a deduplicated ContextPackage respecting token budgets."""

    def __init__(
        self,
        token_budget: int = settings.RETRIEVAL_CONTEXT_TOKEN_BUDGET,
        token_estimator: Optional[TokenEstimator] = None,
    ):
        """Initializes ContextBuilder with a maximum token budget ceiling.

        Args:
            token_budget (int): Maximum token budget ceiling (default 2000).
            token_estimator (Optional[TokenEstimator]): Token estimator instance.
        """
        self.token_budget = token_budget
        self.token_estimator = token_estimator or TokenEstimator()

    def _format_source_citation(self, item: SearchResult) -> str:
        """Formats source citation string e.g. 'annual_report.pdf Page 42'."""
        pages_str = ", ".join(str(p) for p in item.page_numbers) if item.page_numbers else "1"
        return f"{item.document_name} Page {pages_str}"

    def build_context(
        self,
        reranked_results: List[SearchResult],
        token_budget: Optional[int] = None,
    ) -> ContextPackage:
        """Builds a ContextPackage from reranked search results.

        Args:
            reranked_results (List[SearchResult]): List of reranked SearchResult matches.
            token_budget (Optional[int]): Custom token budget override.

        Returns:
            ContextPackage: Synthesized ContextPackage domain model.

        Raises:
            ContextBuilderError: If context assembly fails.
        """
        max_budget = token_budget if token_budget is not None else self.token_budget
        if not reranked_results:
            logger.warning("ContextBuilder received empty reranked results.")
            return ContextPackage(
                context_text="",
                estimated_tokens=0,
                chunks_used=0,
                sources=[],
                source_chunks=[],
                metadata={"status": "EMPTY"},
            )

        logger.info(
            f"Building context from {len(reranked_results)} reranked results "
            f"(token_budget={max_budget})..."
        )

        try:
            seen_chunk_ids: Set[str] = set()
            used_chunks: List[SearchResult] = []
            formatted_sources: List[str] = []
            seen_sources: Set[str] = set()
            context_blocks: List[str] = []

            accumulated_tokens = 0

            for rank_idx, item in enumerate(reranked_results, start=1):
                # 1. Deduplicate by chunk_id
                if item.chunk_id in seen_chunk_ids:
                    continue

                # Estimate chunk tokens
                chunk_tokens = item.estimated_tokens or self.token_estimator.estimate_tokens(item.content)

                # 3. Respect token budget
                if accumulated_tokens + chunk_tokens > max_budget and used_chunks:
                    logger.info(
                        f"Reached token budget ceiling ({accumulated_tokens} + {chunk_tokens} > {max_budget}). "
                        f"Stopping context inclusion at chunk #{rank_idx}."
                    )
                    break

                seen_chunk_ids.add(item.chunk_id)
                used_chunks.append(item)

                # Format source citation
                source_citation = self._format_source_citation(item)
                if source_citation not in seen_sources:
                    seen_sources.add(source_citation)
                    formatted_sources.append(source_citation)

                # Construct structured context block
                header = (
                    f"--- Source [{rank_idx}]: {item.document_name} | "
                    f"Page {', '.join(str(p) for p in item.page_numbers)} | "
                    f"Section: {item.section_title} ---"
                )
                block = f"{header}\n{item.content}\n"
                context_blocks.append(block)

                accumulated_tokens += chunk_tokens

            synthesized_text = "\n".join(context_blocks).strip()
            final_tokens = self.token_estimator.estimate_tokens(synthesized_text)

            logger.info(
                f"Successfully built ContextPackage: {len(used_chunks)} chunks used, "
                f"{len(formatted_sources)} sources, {final_tokens} estimated tokens."
            )

            return ContextPackage(
                context_text=synthesized_text,
                estimated_tokens=final_tokens,
                chunks_used=len(used_chunks),
                sources=formatted_sources,
                source_chunks=used_chunks,
                metadata={
                    "token_budget": max_budget,
                    "token_utilization": round((final_tokens / max_budget) * 100, 2) if max_budget > 0 else 0.0,
                },
            )

        except Exception as e:
            logger.error(f"Context building failed: {e}")
            raise ContextBuilderError(f"Failed to build context package: {str(e)}") from e
