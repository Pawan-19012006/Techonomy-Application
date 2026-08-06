"""Embedding Normalizer for L2 vector unit-length normalization."""

from typing import List
import numpy as np

from app.knowledge.exceptions import EmbeddingNormalizerError
from app.knowledge.models.embedding import Embedding
from app.utils.logging import logger


class EmbeddingNormalizer:
    """Performs L2 unit-length normalization on dense vector embeddings."""

    @classmethod
    def normalize(cls, embeddings: List[Embedding]) -> List[Embedding]:
        """Normalizes each Embedding vector in the list to L2 unit length.

        Args:
            embeddings (List[Embedding]): Input list of Embedding domain objects.

        Returns:
            List[Embedding]: Normalized Embedding domain objects (normalized=True).

        Raises:
            EmbeddingNormalizerError: If normalization fails.
        """
        if not embeddings:
            return []

        logger.debug(f"L2 normalizing {len(embeddings)} vector embeddings...")

        try:
            # Extract raw vectors as 2D NumPy array
            vec_array = np.array([emb.vector for emb in embeddings], dtype=np.float32)

            # Compute L2 norms per row: sqrt(sum(v^2))
            norms = np.linalg.norm(vec_array, axis=1, keepdims=True)

            # Avoid division by zero
            norms[norms == 0] = 1e-12

            # Perform row-wise L2 normalization
            normalized_array = vec_array / norms

            normalized_embeddings: List[Embedding] = []
            for idx, emb in enumerate(embeddings):
                normalized_embeddings.append(
                    Embedding(
                        chunk_id=emb.chunk_id,
                        vector=normalized_array[idx].tolist(),
                        dimension=emb.dimension,
                        normalized=True,
                    )
                )

            logger.info(f"Successfully L2 normalized {len(normalized_embeddings)} vectors.")
            return normalized_embeddings

        except Exception as e:
            logger.error(f"Embedding normalization failed: {e}")
            raise EmbeddingNormalizerError(f"Failed to normalize embeddings: {str(e)}") from e
