"""Query Embedder for generating L2-normalized vector embeddings for search queries."""

from typing import List, Optional
import numpy as np

from app.config import settings
from app.knowledge.exceptions import QueryEmbedderError
from app.knowledge.indexing.embedder import EmbeddingGenerator
from app.knowledge.models.processed_query import ProcessedQuery
from app.utils.logging import logger


class QueryEmbedder:
    """Generates L2-normalized vector embeddings for user search queries using the local BAAI/bge-small-en-v1.5 model."""

    def __init__(
        self,
        embedder: Optional[EmbeddingGenerator] = None,
        model_name: str = settings.EMBEDDING_MODEL_NAME,
    ):
        """Initializes QueryEmbedder using an existing or shared EmbeddingGenerator instance.

        Args:
            embedder (Optional[EmbeddingGenerator]): Shared EmbeddingGenerator instance.
            model_name (str): SentenceTransformers model name.
        """
        self.embedder = embedder or EmbeddingGenerator(model_name=model_name)

    def get_dimension(self) -> int:
        """Returns the embedding vector dimension length.

        Returns:
            int: Vector dimension (e.g. 384).
        """
        return self.embedder.get_dimension()

    def embed_query(self, query: ProcessedQuery) -> List[float]:
        """Generates an L2-normalized dense vector embedding for a ProcessedQuery object.

        Args:
            query (ProcessedQuery): Processed query object.

        Returns:
            List[float]: L2-normalized dense float vector.

        Raises:
            QueryEmbedderError: If embedding generation fails.
        """
        if not query.normalized_query:
            raise QueryEmbedderError("Cannot embed an empty query.")

        logger.info(f"Generating query embedding for '{query.normalized_query[:60]}...'...")

        try:
            model = self.embedder.get_model()

            # Encode query text
            raw_vec = model.encode(
                query.normalized_query,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=False,
            )

            # L2 Unit Normalization
            norm = np.linalg.norm(raw_vec)
            if norm > 0:
                normalized_vec = (raw_vec / norm).tolist()
            else:
                normalized_vec = raw_vec.tolist()

            logger.info(
                f"Successfully generated L2-normalized query vector "
                f"({len(normalized_vec)} float dimensions)."
            )
            return normalized_vec

        except Exception as e:
            logger.error(f"Query embedding generation failed: {e}")
            raise QueryEmbedderError(f"Failed to embed query: {str(e)}") from e
