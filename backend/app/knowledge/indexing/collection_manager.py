"""Collection Manager for creating, verifying, and managing Qdrant collections."""

from typing import Any, Dict, Optional
from app.config import settings
from app.knowledge.exceptions import CollectionManagerError
from app.knowledge.indexing.qdrant_client import QdrantClientWrapper
from app.utils.logging import logger


class CollectionManager:
    """Manages Qdrant collection lifecycle, schema verification, and dimension validation."""

    def __init__(
        self,
        client_wrapper: Optional[QdrantClientWrapper] = None,
        collection_name: str = settings.QDRANT_COLLECTION_NAME,
        distance_metric: str = settings.QDRANT_DISTANCE_METRIC,
    ):
        """Initializes CollectionManager with a client wrapper and collection settings.

        Args:
            client_wrapper (Optional[QdrantClientWrapper]): Client wrapper instance.
            collection_name (str): Collection name (default 'company_knowledge').
            distance_metric (str): Distance metric string ('Cosine').
        """
        self.client_wrapper = client_wrapper or QdrantClientWrapper()
        self.collection_name = collection_name
        self.distance_metric = distance_metric

    def ensure_collection(
        self,
        embedding_dimension: int,
        recreate: bool = False,
    ) -> bool:
        """Ensures the collection exists with correct embedding dimension and distance metric.

        Args:
            embedding_dimension (int): Vector dimension length (e.g. 384).
            recreate (bool): If True, forces collection deletion and re-creation.

        Returns:
            bool: True if collection is ready.

        Raises:
            CollectionManagerError: If collection creation or verification fails.
        """
        if embedding_dimension <= 0:
            logger.error(f"Invalid embedding_dimension={embedding_dimension}")
            raise CollectionManagerError(f"Embedding dimension must be positive, got {embedding_dimension}")

        logger.info(
            f"Ensuring Qdrant collection '{self.collection_name}' "
            f"(dim={embedding_dimension}, metric={self.distance_metric}, recreate={recreate})..."
        )

        try:
            success = self.client_wrapper.create_collection(
                collection_name=self.collection_name,
                vector_size=embedding_dimension,
                distance_metric=self.distance_metric,
                recreate=recreate,
            )
            if not success:
                raise CollectionManagerError(f"Could not create or verify collection '{self.collection_name}'")

            logger.info(f"Collection '{self.collection_name}' is verified and ready for indexing.")
            return True

        except Exception as e:
            logger.error(f"CollectionManager failed for '{self.collection_name}': {e}")
            raise CollectionManagerError(f"Failed to ensure collection '{self.collection_name}': {str(e)}") from e

    def get_info(self) -> Dict[str, Any]:
        """Retrieves collection statistics and metadata.

        Returns:
            Dict[str, Any]: Metadata dictionary containing status and point count.
        """
        return self.client_wrapper.collection_info(self.collection_name)
