#!/usr/bin/env python3
"""Pre-event model pre-caching script for Techonomy deployment readiness.

Downloads and warms up required local SentenceTransformer embedding models
so the application can run offline during event execution without internet access.
"""

import sys
import time
from pathlib import Path

# Ensure backend directory is in Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.knowledge.indexing.embedder import EmbeddingGenerator
from app.utils.logging import logger


def main() -> int:
    """Preloads and warms up all required local ML models."""
    model_name = settings.EMBEDDING_MODEL_NAME
    logger.info(f"=== Starting Techonomy Model Pre-Caching Script ===")
    logger.info(f"Target Embedding Model: '{model_name}'")

    t_start = time.perf_counter()

    try:
        generator = EmbeddingGenerator(model_name=model_name)
        model_inst = generator.get_model()

        # Warmup dummy encoding pass
        test_text = "Techonomy pre-event deployment readiness model verification query."
        vec = model_inst.encode([test_text], show_progress_bar=False)

        duration = time.perf_counter() - t_start
        dimension = generator.get_dimension()

        cache_status = "LOADED FROM LOCAL CACHE" if duration < 0.8 else "DOWNLOADED AND CACHED"

        logger.info(
            f"\n==========================================\n"
            f"[PRELOAD SUCCESS]\n"
            f"Model Name: {model_name}\n"
            f"Status: {cache_status}\n"
            f"Vector Dimension: {dimension}\n"
            f"Total Duration: {duration:.3f}s\n"
            f"Sample Vector Shape: {vec.shape}\n"
            f"=========================================="
        )
        print(f"SUCCESS: Model '{model_name}' is fully cached and ready for offline deployment.")
        return 0

    except Exception as e:
        logger.error(f"[PRELOAD FAILED] Could not pre-cache model '{model_name}': {e}")
        print(f"ERROR: Failed to preload model '{model_name}': {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
