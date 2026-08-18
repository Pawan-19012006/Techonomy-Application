"""Result Reranker using lightweight heuristic scoring and keyword boost."""

import re
from typing import List, Optional, Set
from app.config import settings
from app.knowledge.exceptions import RerankerError
from app.knowledge.models.processed_query import ProcessedQuery
from app.knowledge.models.search_result import SearchResult
from app.utils.logging import logger


class Reranker:
    """Reranks initial vector search results using hybrid semantic similarity and heuristic keyword boosts."""

    def __init__(
        self,
        top_n: int = settings.RETRIEVAL_RERANK_TOP_N,
        semantic_weight: float = 0.75,
        keyword_weight: float = 0.15,
        title_boost: float = 0.10,
        heading_boost: float = 0.05,
    ):
        """Initializes Reranker weights and selection count.

        Args:
            top_n (int): Number of top reranked matches to return (default 5).
            semantic_weight (float): Weight assigned to vector cosine similarity score.
            keyword_weight (float): Weight assigned to exact word overlap.
            title_boost (float): Score boost if query words match section title.
            heading_boost (float): Score boost if chunk section type is heading.
        """
        self.top_n = top_n
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        self.title_boost = title_boost
        self.heading_boost = heading_boost

    def _extract_words(self, text: str) -> Set[str]:
        """Helper to extract lowercase alphanumeric token words."""
        return set(re.findall(r"\w+", text.lower()))

    def rerank(
        self,
        results: List[SearchResult],
        query: ProcessedQuery,
        top_n: Optional[int] = None,
    ) -> List[SearchResult]:
        """Reranks input SearchResult list and returns top_n matches sorted by combined score descending.

        Args:
            results (List[SearchResult]): Initial vector search matches.
            query (ProcessedQuery): Processed query object.
            top_n (Optional[int]): Custom top_n override.

        Returns:
            List[SearchResult]: Top N reranked SearchResult matches.

        Raises:
            RerankerError: If reranking execution fails.
        """
        if not results:
            return []

        limit_n = top_n if top_n is not None else self.top_n
        logger.info(f"Reranking {len(results)} search results (selecting top_n={limit_n})...")

        try:
            query_words = self._extract_words(query.normalized_query)
            if not query_words:
                return results[:limit_n]

            reranked: List[SearchResult] = []

            for item in results:
                # 1. Base semantic score
                sem_score = item.score

                # 2. Keyword overlap score
                content_words = self._extract_words(item.content)
                overlap_count = len(query_words.intersection(content_words))
                kw_score = overlap_count / len(query_words) if query_words else 0.0

                # 3. Section title boost
                title_words = self._extract_words(item.section_title)
                title_match = any(w in title_words for w in query_words)
                t_boost = self.title_boost if title_match else 0.0

                # 4. Heading boost
                is_heading = item.section_type in ("heading", "title") or item.hierarchy_level <= 2
                h_boost = self.heading_boost if is_heading else 0.0

                # 5. Numerical & Analytical Evidence Density Boost
                content_lower = item.content.lower()
                num_matches = len(re.findall(r"\b\d+(?:\.\d+)?%?|\b(?:revenue|ebitda|profit|margin|income|cogs|growth|operating|lakh|crore|thousand)\b", content_lower))
                n_boost = min(0.15, num_matches * 0.025) if any(w in query_words for w in ["financial", "performance", "revenue", "profit", "ebitda", "margin", "growth", "cost", "vendor", "sales", "period", "compare"]) else 0.0

                # 6. Structured Financial Table & Multi-Period Metric Boost
                table_lines = [
                    line for line in item.content.split("\n")
                    if any(m in line.lower() for m in ["revenue", "profit", "margin", "ebit", "operating", "cogs", "expenses", "sales", "net"])
                    and any(char.isdigit() for char in line)
                ]
                t_table_boost = 0.18 if len(table_lines) >= 2 else (0.10 if len(table_lines) == 1 else 0.0)

                # Calculate composite hybrid score
                final_score = (
                    (self.semantic_weight * sem_score)
                    + (self.keyword_weight * kw_score)
                    + t_boost
                    + h_boost
                    + n_boost
                    + t_table_boost
                )

                # Clone SearchResult with updated reranked score
                reranked_item = SearchResult(
                    chunk_id=item.chunk_id,
                    document_id=item.document_id,
                    document_name=item.document_name,
                    document_type=getattr(item, "document_type", "company"),
                    visibility=getattr(item, "visibility", "user_visible"),
                    score=round(final_score, 4),
                    content=item.content,
                    page_numbers=item.page_numbers,
                    section_title=item.section_title,
                    section_type=item.section_type,
                    hierarchy_level=item.hierarchy_level,
                    reading_order=item.reading_order,
                    estimated_tokens=item.estimated_tokens,
                    payload=item.payload,
                )
                reranked.append(reranked_item)

            # Sort by combined score descending
            reranked.sort(key=lambda x: x.score, reverse=True)

            # Diversity selection: Max 2 chunks per document in top_n final selection
            selected: List[SearchResult] = []
            selected_doc_counts = {}
            for candidate in reranked:
                dname = candidate.document_name
                if selected_doc_counts.get(dname, 0) < 2 or len(selected) < limit_n // 2:
                    selected.append(candidate)
                    selected_doc_counts[dname] = selected_doc_counts.get(dname, 0) + 1

                if len(selected) >= limit_n:
                    break

            # Fallback if diversity selection yielded fewer than limit_n
            if len(selected) < limit_n:
                for candidate in reranked:
                    if candidate not in selected:
                        selected.append(candidate)
                        if len(selected) >= limit_n:
                            break

            logger.info(f"Successfully reranked {len(results)} results into top {len(selected)} matches across {len(selected_doc_counts)} documents.")
            return selected

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            raise RerankerError(f"Reranker error: {str(e)}") from e
