"""Local Embedding Generator using SentenceTransformers with thread-safe application-lifetime singleton loading."""

import threading
import time
from typing import Any, List, Optional

from app.config import settings
from app.knowledge.exceptions import EmbeddingGeneratorError
from app.knowledge.models.embedding import Embedding
from app.knowledge.models.knowledge_chunk import KnowledgeChunk
from app.utils.logging import logger

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


class EmbeddingGenerator:
    """Generates dense vector embeddings locally using SentenceTransformers models with thread-safe memory residency."""

    _model_instance: Optional[Any] = None  # SentenceTransformer instance
    _loaded_model_name: Optional[str] = None
    _lock: threading.Lock = threading.Lock()
    _load_time_seconds: float = 0.0

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL_NAME):
        """Initializes EmbeddingGenerator with model name setting."""
        self.model_name = model_name

    @classmethod
    def preload_model(cls, model_name: str = settings.EMBEDDING_MODEL_NAME) -> None:
        """Preloads and warms up the model during application startup."""
        inst = cls(model_name=model_name)
        inst.get_model()

    def get_model(self) -> Any:
        """Loads and caches the SentenceTransformers model instance in memory (Thread-safe Singleton)."""
        if (
            EmbeddingGenerator._model_instance is None
            or EmbeddingGenerator._loaded_model_name != self.model_name
        ):
            with EmbeddingGenerator._lock:
                # Double-check inside lock
                if (
                    EmbeddingGenerator._model_instance is None
                    or EmbeddingGenerator._loaded_model_name != self.model_name
                ):
                    t0 = time.perf_counter()
                    logger.info(f"Loading local SentenceTransformer model '{self.model_name}'...")
                    try:
                        from sentence_transformers import SentenceTransformer
                        EmbeddingGenerator._model_instance = SentenceTransformer(self.model_name)
                        EmbeddingGenerator._loaded_model_name = self.model_name
                        EmbeddingGenerator._load_time_seconds = time.perf_counter() - t0

                        # Warmup dummy encode to force CUDA/CPU tensor initialization
                        _ = EmbeddingGenerator._model_instance.encode(["warmup query"], show_progress_bar=False)

                        dim = self.get_dimension()
                        logger.info(
                            f"\n[EMBEDDING]\n"
                            f"model={self.model_name}\n"
                            f"status=loaded\n"
                            f"dimension={dim}\n"
                            f"load_time={EmbeddingGenerator._load_time_seconds:.3f}s"
                        )
                    except Exception as e:
                        logger.error(f"Failed to load embedding model '{self.model_name}': {e}")
                        raise EmbeddingGeneratorError(f"Error loading model '{self.model_name}': {str(e)}") from e

        return EmbeddingGenerator._model_instance

    def get_dimension(self) -> int:
        """Obtains vector embedding dimension dynamically from loaded model."""
        model = self.get_model()
        if hasattr(model, "get_embedding_dimension"):
            return model.get_embedding_dimension()
        return model.get_sentence_embedding_dimension()

    def encode_text(self, text: str) -> Any:
        """Encodes single query text with inference optimization and timing."""
        t0 = time.perf_counter()
        model = self.get_model()

        if HAS_TORCH:
            with torch.no_grad():
                raw_vec = model.encode(
                    text,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    normalize_embeddings=False,
                )
        else:
            raw_vec = model.encode(
                text,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=False,
            )

        duration = time.perf_counter() - t0
        logger.debug(
            f"\n[EMBEDDING]\n"
            f"query='{text[:40]}...'\n"
            f"duration={duration:.4f}s\n"
            f"cache_hit=False"
        )
        return raw_vec

    def generate_embeddings(
        self,
        chunks: List[KnowledgeChunk],
        batch_size: int = settings.EMBEDDING_BATCH_SIZE,
    ) -> List[Embedding]:
        """Generates dense vector embeddings for KnowledgeChunks in batches."""
        if not chunks:
            return []

        logger.info(
            f"Generating embeddings for {len(chunks)} chunks using model '{self.model_name}' "
            f"(batch_size={batch_size})..."
        )

        try:
            model = self.get_model()
            texts = [c.content for c in chunks]

            if HAS_TORCH:
                with torch.no_grad():
                    vectors_np = model.encode(
                        texts,
                        batch_size=batch_size,
                        show_progress_bar=False,
                        convert_to_numpy=True,
                        normalize_embeddings=False,
                    )
            else:
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
