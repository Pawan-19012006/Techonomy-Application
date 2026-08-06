"""Qdrant Client Wrapper providing robust vector database operations."""

from typing import Any, Dict, List, Optional
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest_models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import settings
from app.knowledge.exceptions import QdrantClientWrapperError
from app.knowledge.models.indexed_chunk import IndexedChunk
from app.utils.logging import logger


class QdrantClientWrapper:
    """Wrapper around qdrant-client providing collection lifecycle and point upsert methods."""

    def __init__(
        self,
        host: str = settings.QDRANT_HOST,
        port: int = settings.QDRANT_PORT,
        storage_path: Optional[str] = settings.QDRANT_STORAGE_PATH,
    ):
        """Initializes Qdrant Client configuration.

        Args:
            host (str): Qdrant server host.
            port (int): Qdrant server port.
            storage_path (Optional[str]): Local disk storage path fallback.
        """
        self.host = host
        self.port = port
        self.storage_path = storage_path
        self._client: Optional[QdrantClient] = None

    def connect(self) -> QdrantClient:
        """Establishes connection to Qdrant server, falling back to local storage if server unavailable.

        Returns:
            QdrantClient: Active Qdrant client instance.

        Raises:
            QdrantClientWrapperError: If connection initialization fails.
        """
        if self._client is not None:
            return self._client

        logger.info(f"Connecting to Qdrant at '{self.host}:{self.port}'...")

        try:
            # Try connecting to HTTP server host/port
            client = QdrantClient(host=self.host, port=self.port, timeout=2.0)
            client.get_collections()
            self._client = client
            logger.info(f"Successfully connected to Qdrant server at '{self.host}:{self.port}'.")
            return self._client
        except Exception as e:
            logger.warning(
                f"Could not connect to live Qdrant server at '{self.host}:{self.port}' ({e}). "
                f"Falling back to local disk storage at '{self.storage_path}'..."
            )
            try:
                # Local disk storage fallback
                self._client = QdrantClient(path=self.storage_path)
                logger.info(f"Successfully initialized local Qdrant engine at '{self.storage_path}'.")
                return self._client
            except Exception as fallback_err:
                logger.warning(
                    f"Local disk storage failed ({fallback_err}). Falling back to in-memory Qdrant instance..."
                )
                try:
                    self._client = QdrantClient(location=":memory:")
                    logger.info("Successfully initialized in-memory Qdrant client.")
                    return self._client
                except Exception as mem_err:
                    logger.error(f"Failed to initialize Qdrant client: {mem_err}")
                    raise QdrantClientWrapperError(f"Qdrant connection failed: {str(mem_err)}") from mem_err

    def health_check(self) -> bool:
        """Verifies Qdrant client connectivity and operational health.

        Returns:
            bool: True if client is healthy.
        """
        try:
            client = self.connect()
            client.get_collections()
            return True
        except Exception as e:
            logger.warning(f"Qdrant health check failed: {e}")
            return False

    def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance_metric: str = "Cosine",
        recreate: bool = False,
    ) -> bool:
        """Creates vector collection if missing or recreates if requested.

        Args:
            collection_name (str): Name of target collection.
            vector_size (int): Dimension of vectors (e.g. 384).
            distance_metric (str): Distance function ('Cosine', 'Euclid', 'Dot').
            recreate (bool): If True, deletes existing collection before creation.

        Returns:
            bool: True if collection created or already exists.

        Raises:
            QdrantClientWrapperError: If collection creation fails.
        """
        client = self.connect()

        # Map distance metric string to Qdrant Distance enum
        metric_upper = distance_metric.upper()
        if metric_upper == "COSINE":
            dist_enum = rest_models.Distance.COSINE
        elif metric_upper in ("EUCLID", "EUCLIDEAN"):
            dist_enum = rest_models.Distance.EUCLID
        elif metric_upper == "DOT":
            dist_enum = rest_models.Distance.DOT
        else:
            dist_enum = rest_models.Distance.COSINE

        try:
            # Check if collection exists
            collections_res = client.get_collections()
            existing_names = [c.name for c in collections_res.collections]

            if collection_name in existing_names:
                if recreate:
                    logger.info(f"Recreating collection '{collection_name}'...")
                    client.delete_collection(collection_name=collection_name)
                else:
                    logger.info(f"Collection '{collection_name}' already exists.")
                    return True

            logger.info(
                f"Creating Qdrant collection '{collection_name}' "
                f"(size={vector_size}, distance={dist_enum})..."
            )
            client.create_collection(
                collection_name=collection_name,
                vectors_config=rest_models.VectorParams(
                    size=vector_size,
                    distance=dist_enum,
                ),
            )
            logger.info(f"Collection '{collection_name}' created successfully.")
            return True

        except Exception as e:
            logger.error(f"Failed to create collection '{collection_name}': {e}")
            raise QdrantClientWrapperError(f"Error creating collection '{collection_name}': {str(e)}") from e

    def upsert_chunks(
        self,
        collection_name: str,
        indexed_chunks: List[IndexedChunk],
        batch_size: int = settings.EMBEDDING_BATCH_SIZE,
    ) -> int:
        """Upserts list of IndexedChunk objects into Qdrant collection.

        Args:
            collection_name (str): Target collection name.
            indexed_chunks (List[IndexedChunk]): List of IndexedChunk objects containing vector and payload.
            batch_size (int): Max points per upsert request batch.

        Returns:
            int: Number of points successfully uploaded.

        Raises:
            QdrantClientWrapperError: If upsert operation fails.
        """
        if not indexed_chunks:
            return 0

        client = self.connect()
        logger.info(f"Upserting {len(indexed_chunks)} vectors to Qdrant collection '{collection_name}'...")

        try:
            total_uploaded = 0
            points: List[rest_models.PointStruct] = []

            for ichk in indexed_chunks:
                # Convert string chunk_id to UUID string or integer ID for Qdrant compatibility
                try:
                    point_id = str(uuid.UUID(ichk.embedding.chunk_id))
                except ValueError:
                    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, ichk.embedding.chunk_id))

                points.append(
                    rest_models.PointStruct(
                        id=point_id,
                        vector=ichk.embedding.vector,
                        payload=ichk.payload,
                    )
                )

            # Upload in batches
            for i in range(0, len(points), batch_size):
                batch_points = points[i : i + batch_size]
                client.upsert(
                    collection_name=collection_name,
                    points=batch_points,
                )
                total_uploaded += len(batch_points)

            logger.info(f"Successfully uploaded {total_uploaded} points to '{collection_name}'.")
            return total_uploaded

        except Exception as e:
            logger.error(f"Failed to upsert vectors to '{collection_name}': {e}")
            raise QdrantClientWrapperError(f"Upsert to '{collection_name}' failed: {str(e)}") from e

    def delete_document(self, collection_name: str, document_id: str) -> bool:
        """Deletes all vector points matching document_id from collection.

        Args:
            collection_name (str): Target collection name.
            document_id (str): UUID document_id to delete.

        Returns:
            bool: True if deletion command completed.
        """
        client = self.connect()
        logger.info(f"Deleting document '{document_id}' points from collection '{collection_name}'...")

        try:
            client.delete(
                collection_name=collection_name,
                points_selector=rest_models.FilterSelector(
                    filter=rest_models.Filter(
                        must=[
                            rest_models.FieldCondition(
                                key="document_id",
                                match=rest_models.MatchValue(value=document_id),
                            )
                        ]
                    )
                ),
            )
            logger.info(f"Deleted points for document '{document_id}' from '{collection_name}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document '{document_id}': {e}")
            raise QdrantClientWrapperError(f"Delete document '{document_id}' failed: {str(e)}") from e

    def collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Retrieves collection statistics and configuration metadata.

        Args:
            collection_name (str): Target collection name.

        Returns:
            Dict[str, Any]: Collection info metadata dictionary.
        """
        client = self.connect()

        try:
            info = client.get_collection(collection_name=collection_name)
            return {
                "name": collection_name,
                "status": str(info.status),
                "vectors_count": info.vectors_count if hasattr(info, "vectors_count") else info.points_count,
                "points_count": info.points_count,
            }
        except UnexpectedResponse as e:
            logger.warning(f"Collection '{collection_name}' not found: {e}")
            return {"name": collection_name, "status": "NOT_FOUND", "vectors_count": 0, "points_count": 0}
        except Exception as e:
            logger.error(f"Error fetching info for collection '{collection_name}': {e}")
            raise QdrantClientWrapperError(f"Failed to fetch info for '{collection_name}': {str(e)}") from e

    def count_vectors(self, collection_name: str) -> int:
        """Returns aggregate vector count in a collection.

        Args:
            collection_name (str): Target collection name.

        Returns:
            int: Vector count.
        """
        info = self.collection_info(collection_name)
        return info.get("vectors_count") or info.get("points_count") or 0
