"""Index Manager orchestrating the full Phase 4 Knowledge Indexing Engine pipeline."""

import time
from typing import List, Optional, Tuple
from app.config import settings
from app.knowledge.exceptions import IndexManagerError
from app.knowledge.indexing.collection_manager import CollectionManager
from app.knowledge.indexing.embedder import EmbeddingGenerator
from app.knowledge.indexing.embedding_normalizer import EmbeddingNormalizer
from app.knowledge.indexing.payload_builder import PayloadBuilder
from app.knowledge.indexing.qdrant_client import QdrantClientWrapper
from app.knowledge.models.index_result import IndexResult
from app.knowledge.models.knowledge_chunk import KnowledgeChunk
from app.utils.logging import logger


class IndexManager:
    """Orchestrates Phase 4 indexing pipeline: KnowledgeChunks -> Embeddings -> Normalizer -> Payload -> Qdrant Indexer."""

    def __init__(
        self,
        embedder: Optional[EmbeddingGenerator] = None,
        normalizer: Optional[EmbeddingNormalizer] = None,
        payload_builder: Optional[PayloadBuilder] = None,
        collection_manager: Optional[CollectionManager] = None,
        client_wrapper: Optional[QdrantClientWrapper] = None,
        collection_name: str = settings.QDRANT_COLLECTION_NAME,
    ):
        """Initializes IndexManager dependencies."""
        self.embedder = embedder or EmbeddingGenerator()
        self.normalizer = normalizer or EmbeddingNormalizer()
        self.payload_builder = payload_builder or PayloadBuilder()
        self.client_wrapper = client_wrapper or QdrantClientWrapper()
        self.collection_manager = collection_manager or CollectionManager(
            client_wrapper=self.client_wrapper,
            collection_name=collection_name,
        )
        self.collection_name = collection_name

    def index_chunks(
        self,
        chunks: List[KnowledgeChunk],
        document_name: Optional[str] = None,
        recreate_collection: bool = False,
    ) -> IndexResult:
        """Executes full indexing pipeline for a list of KnowledgeChunk objects.

        Pipeline Steps:
            1. Obtain embedding dimension from model.
            2. Ensure Qdrant collection exists and has correct dimensions.
            3. Generate dense vector embeddings locally.
            4. L2 normalize embedding vectors.
            5. Serialize chunks and metadata into Qdrant payloads.
            6. Upsert vectors and payloads to Qdrant collection.
            7. Verify uploaded points count.

        Args:
            chunks (List[KnowledgeChunk]): Input list of KnowledgeChunk objects.
            document_name (Optional[str]): Document filename or title.
            recreate_collection (bool): If True, re-creates the collection before indexing.

        Returns:
            IndexResult: Indexing result summary object.

        Raises:
            IndexManagerError: If indexing pipeline fails.
        """
        if not chunks:
            logger.warning("IndexManager received empty chunks list.")
            return IndexResult(
                documents_indexed=0,
                chunks_indexed=0,
                vectors_uploaded=0,
                collection_name=self.collection_name,
                embedding_dimension=self.embedder.get_dimension(),
                processing_time=0.0,
            )

        start_time = time.time()
        logger.info(f"=== Starting Knowledge Indexing Engine for {len(chunks)} chunks ===")

        try:
            # Step 1 & 2: Embedding Dimension & Collection Management
            dimension = self.embedder.get_dimension()
            self.collection_manager.ensure_collection(
                embedding_dimension=dimension,
                recreate=recreate_collection,
            )

            # Step 3: Generate Local Embeddings
            raw_embeddings = self.embedder.generate_embeddings(chunks)

            # Step 4: L2 Normalize Vectors
            normalized_embeddings = self.normalizer.normalize(raw_embeddings)

            # Step 5: Payload Serialization
            indexed_chunks = self.payload_builder.build_indexed_chunks(
                chunks=chunks,
                embeddings=normalized_embeddings,
                document_name=document_name,
            )

            # Step 6: Qdrant Upsert
            uploaded_count = self.client_wrapper.upsert_chunks(
                collection_name=self.collection_name,
                indexed_chunks=indexed_chunks,
            )

            # Calculate metrics
            unique_docs = len({c.document_id for c in chunks})
            elapsed = time.time() - start_time

            result = IndexResult(
                documents_indexed=unique_docs,
                chunks_indexed=len(chunks),
                vectors_uploaded=uploaded_count,
                collection_name=self.collection_name,
                embedding_dimension=dimension,
                processing_time=round(elapsed, 3),
            )

            logger.info(
                f"=== Completed Knowledge Indexing Engine === "
                f"[Uploaded: {uploaded_count} vectors, Dim: {dimension}, Time: {result.processing_time}s]"
            )
            return result

        except Exception as e:
            logger.error(f"Indexing pipeline failed: {e}")
            raise IndexManagerError(f"Failed to index chunks: {str(e)}") from e
