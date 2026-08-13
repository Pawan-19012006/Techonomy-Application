"""Thread-safe bounded TTL cache for query embeddings."""

from collections import OrderedDict
import re
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from app.config import settings
from app.utils.logging import logger


class QueryEmbeddingCache:
    """Thread-safe bounded LRU + TTL in-process cache for dense vector embeddings."""

    def __init__(
        self,
        enabled: bool = settings.QUERY_EMBEDDING_CACHE_ENABLED,
        max_size: int = settings.QUERY_EMBEDDING_CACHE_SIZE,
        ttl_seconds: int = settings.QUERY_EMBEDDING_CACHE_TTL_SECONDS,
    ):
        """Initializes QueryEmbeddingCache with bounds and lock."""
        self.enabled = enabled
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Tuple[List[float], float]] = OrderedDict()
        self._lock = threading.Lock()

        # Metrics
        self.hits = 0
        self.misses = 0

    @staticmethod
    def normalize_query(query: str) -> str:
        """Normalizes query text for consistent cache lookup."""
        if not query:
            return ""
        # Trim, lowercase, and collapse whitespace
        text = query.strip().lower()
        text = re.sub(r'\s+', ' ', text)
        return text

    def get(self, query: str) -> Optional[List[float]]:
        """Retrieves cached embedding vector if present and unexpired."""
        if not self.enabled:
            return None

        key = self.normalize_query(query)
        if not key:
            return None

        with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None

            vector, timestamp = self._cache[key]
            # Check TTL
            if time.time() - timestamp > self.ttl_seconds:
                del self._cache[key]
                self.misses += 1
                return None

            # Move to end (LRU)
            self._cache.move_to_end(key)
            self.hits += 1
            return vector

    def put(self, query: str, vector: List[float]) -> None:
        """Stores embedding vector in cache with LRU eviction and timestamp."""
        if not self.enabled or not vector:
            return

        key = self.normalize_query(query)
        if not key:
            return

        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (vector, time.time())

            # Enforce max size eviction
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def clear(self) -> None:
        """Clears all cached entries and resets metrics."""
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0

    def metrics(self) -> Dict[str, Any]:
        """Returns cache metrics dictionary."""
        with self._lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total) if total > 0 else 0.0
            return {
                "embedding_cache_enabled": self.enabled,
                "embedding_cache_size": len(self._cache),
                "embedding_cache_max_size": self.max_size,
                "embedding_cache_hits": self.hits,
                "embedding_cache_misses": self.misses,
                "embedding_cache_hit_rate": round(hit_rate, 4),
            }


# Singleton query embedding cache instance
query_embedding_cache = QueryEmbeddingCache()
