"""Local Embedding Generator using SentenceTransformers (BAAI/bge-small-en-v1.5)."""

from typing import List, Optional
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.knowledge.exceptions import EmbeddingGeneratorError
from app.knowledge.models.embedding import Embedding
from app.knowledge.models.knowledge_chunk import KnowledgeChunk
from app.utils.logging import logger


class EmbeddingGenerator:
    """Generates dense vector embeddings locally using SentenceTransformers models."""

    _model_instance: Optional[SentenceTransformer] = None
    _loaded_model_name: Optional[str] = None

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL_NAME):
        """Initializes the EmbeddingGenerator with a specified model name.

        Args:
            model_name (str): SentenceTransformers model name or path.
        """
        self.model_name = model_name

    def get_model(self) -> SentenceTransformer:
        """Loads and caches the SentenceTransformers model instance (Singleton pattern).

        Returns:
            SentenceTransformer: Loaded model instance.

        Raises:
            EmbeddingGeneratorError: If model loading fails.
        """
        if (
            EmbeddingGenerator._model_instance is None
            or EmbeddingGenerator._loaded_model_name != self.model_name
        ):
            logger.info(f"Loading local SentenceTransformer model '{self.model_name}'...")
            try:
                EmbeddingGenerator._model_instance = SentenceTransformer(self.model_name)
                EmbeddingGenerator._loaded_model_name = self.model_name
                logger.info(
                    f"Model '{self.model_name}' loaded successfully. "
                    f"Vector dimension: {self.get_dimension()}"
                )
            except Exception as e:
                logger.error(f"Failed to load model '{self.model_name}': {e}")
                raise EmbeddingGeneratorError(f"Error loading model '{self.model_name}': {str(e)}") from e

        return EmbeddingGenerator._model_instance

    def get_dimension(self) -> int:
        """Obtains vector embedding dimension dynamically from the loaded model.

        Returns:
            int: Vector dimension (e.g. 384 for bge-small-en-v1.5).
        """
        model = self.get_model()
        if hasattr(model, "get_embedding_dimension"):
            return model.get_embedding_dimension()
        return model.get_sentence_embedding_dimension()

    def generate_embeddings(
        self,
        chunks: List[KnowledgeChunk],
        batch_size: int = settings.EMBEDDING_BATCH_SIZE,
    ) -> List[Embedding]:
        """Generates dense vector embeddings for a list of KnowledgeChunk objects in batches.

        Args:
            chunks (List[KnowledgeChunk]): List of input KnowledgeChunk objects.
            batch_size (int): Batch size for model inference.

        Returns:
            List[Embedding]: List of generated Embedding domain objects.

        Raises:
            EmbeddingGeneratorError: If embedding generation fails.
        """
        if not chunks:
            return []

        logger.info(
            f"Generating embeddings for {len(chunks)} chunks using model '{self.model_name}' "
            f"(batch_size={batch_size})..."
        )

        try:
            model = self.get_model()
            texts = [c.content for c in chunks]

            # Run batch inference using SentenceTransformer.encode
            vectors_np = model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=False,
            )

            dimension = self.get_dimension()
            embeddings: List[Embedding] = []

            for idx, chunk in enumerate(chunks):
                vec_list = vectors_np[idx].tolist()
                embeddings.append(
                    Embedding(
                        chunk_id=chunk.chunk_id,
                        vector=vec_list,
                        dimension=dimension,
                        normalized=False,
                    )
                )

            logger.info(f"Successfully generated {len(embeddings)} vector embeddings.")
            return embeddings

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise EmbeddingGeneratorError(f"Failed to generate embeddings: {str(e)}") from e
