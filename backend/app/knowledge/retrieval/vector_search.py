"""Vector Search component for executing dense semantic similarity searches against Qdrant."""

from typing import List, Optional
from app.config import settings
from app.knowledge.exceptions import VectorSearchError
from app.knowledge.indexing.qdrant_client import QdrantClientWrapper
from app.knowledge.models.search_result import SearchResult
from app.knowledge.retrieval.search_filters import SearchFilters
from app.utils.logging import logger


class VectorSearch:
    """Executes dense vector similarity searches against Qdrant collections."""

    def __init__(
        self,
        client_wrapper: Optional[QdrantClientWrapper] = None,
        collection_name: str = settings.QDRANT_COLLECTION_NAME,
    ):
        """Initializes VectorSearch with Qdrant client wrapper and collection target.

        Args:
            client_wrapper (Optional[QdrantClientWrapper]): Client wrapper instance.
            collection_name (str): Collection name (default 'company_knowledge').
        """
        self.client_wrapper = client_wrapper or QdrantClientWrapper()
        self.collection_name = collection_name

    def search(
        self,
        query_vector: List[float],
        top_k: int = settings.RETRIEVAL_TOP_K,
        filters: Optional[SearchFilters] = None,
        min_score: Optional[float] = settings.RETRIEVAL_MINIMUM_SIMILARITY,
        collection_name: Optional[str] = None,
    ) -> List[SearchResult]:
        """Performs dense vector similarity search in Qdrant and maps hits to SearchResult objects."""
        if not query_vector:
            raise VectorSearchError("Query vector cannot be empty.")

        target_collection = collection_name or self.collection_name
        client = self.client_wrapper.connect()
        qdrant_filter = filters.to_qdrant_filter() if filters else None

        min_similarity = (
            filters.minimum_similarity if (filters and filters.minimum_similarity is not None) else min_score
        )

        logger.info(
            f"Executing Qdrant vector search in '{target_collection}' "
            f"(top_k={top_k}, min_similarity={min_similarity})..."
        )

        try:
            # Query Qdrant
            if hasattr(client, "search"):
                hits = client.search(
                    collection_name=target_collection,
                    query_vector=query_vector,
                    limit=top_k,
                    query_filter=qdrant_filter,
                    score_threshold=min_similarity,
                )
            else:
                response = client.query_points(
                    collection_name=target_collection,
                    query=query_vector,
                    limit=top_k,
                    query_filter=qdrant_filter,
                    score_threshold=min_similarity,
                )
                hits = response.points

            results: List[SearchResult] = []
            for hit in hits:
                payload = hit.payload or {}
                chunk_id = payload.get("chunk_id") or str(hit.id)
                doc_id = payload.get("document_id") or "unknown_doc"
                doc_name = payload.get("document_name") or payload.get("metadata", {}).get("filename") or doc_id
                content = payload.get("content", "")
                page_numbers = payload.get("page_numbers", [])
                section_title = payload.get("section_title", "Untitled Section")
                section_type = payload.get("section_type", "composite")
                hierarchy_level = payload.get("hierarchy_level", 2)
                reading_order = payload.get("reading_order", 0)
                estimated_tokens = payload.get("estimated_tokens", 0)

                doc_type = payload.get("document_type") or payload.get("metadata", {}).get("document_type") or "company"
                visibility = payload.get("visibility") or payload.get("metadata", {}).get("visibility") or ("user_visible" if doc_type == "company" else "internal")

                results.append(
                    SearchResult(
                        chunk_id=chunk_id,
                        document_id=doc_id,
                        document_name=doc_name,
                        document_type=doc_type,
                        visibility=visibility,
                        score=float(hit.score),
                        content=content,
                        page_numbers=page_numbers,
                        section_title=section_title,
                        section_type=section_type,
                        hierarchy_level=hierarchy_level,
                        reading_order=reading_order,
                        estimated_tokens=estimated_tokens,
                        payload=payload,
                    )
                )

            logger.info(f"Vector search returned {len(results)} hits matching query.")
            return results

        except Exception as e:
            logger.error(f"Vector search failed in collection '{self.collection_name}': {e}")
            raise VectorSearchError(f"Vector search failed: {str(e)}") from e
