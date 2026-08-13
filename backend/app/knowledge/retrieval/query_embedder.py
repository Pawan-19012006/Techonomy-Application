"""Query Embedder for generating L2-normalized vector embeddings with query embedding caching."""

from typing import List, Optional
import numpy as np

from app.config import settings
from app.knowledge.exceptions import QueryEmbedderError
from app.knowledge.indexing.embedder import EmbeddingGenerator
from app.knowledge.models.processed_query import ProcessedQuery
from app.knowledge.retrieval.query_embedding_cache import query_embedding_cache
from app.utils.logging import logger


class QueryEmbedder:
    """Generates L2-normalized vector embeddings for search queries with thread-safe query embedding caching."""

    def __init__(
        self,
        embedder: Optional[EmbeddingGenerator] = None,
        model_name: str = settings.EMBEDDING_MODEL_NAME,
    ):
        """Initializes QueryEmbedder using EmbeddingGenerator instance."""
        self.embedder = embedder or EmbeddingGenerator(model_name=model_name)

    def get_dimension(self) -> int:
        """Returns vector embedding dimension."""
        return self.embedder.get_dimension()

    def embed_query(self, query: ProcessedQuery) -> List[float]:
        """Generates L2-normalized dense vector embedding for ProcessedQuery with caching."""
        if not query.normalized_query:
            raise QueryEmbedderError("Cannot embed an empty query.")

        # Check in-memory query embedding cache
        cached_vec = query_embedding_cache.get(query.normalized_query)
        if cached_vec is not None:
            logger.info(f"[EMBEDDING CACHE HIT] Query: '{query.normalized_query[:40]}...'")
            return cached_vec

        try:
            raw_vec = self.embedder.encode_text(query.normalized_query)

            # L2 Unit Normalization
            norm = np.linalg.norm(raw_vec)
            if norm > 0:
                normalized_vec = (raw_vec / norm).tolist()
            else:
                normalized_vec = raw_vec.tolist()

            # Store in cache
            query_embedding_cache.put(query.normalized_query, normalized_vec)
            return normalized_vec

        except Exception as e:
            logger.error(f"Query embedding generation failed: {e}")
            raise QueryEmbedderError(f"Failed to embed query: {str(e)}") from e
