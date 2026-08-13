"""Thread-safe bounded TTL answer cache for bypassing RAG pipelines on repeated questions."""

from collections import OrderedDict
import re
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from app.config import settings
from app.schemas.chat import SourceItem
from app.utils.logging import logger


class AnswerCache:
    """Thread-safe bounded LRU + TTL answer cache for document-grounded RAG questions."""

    def __init__(
        self,
        enabled: bool = settings.ANSWER_CACHE_ENABLED,
        max_size: int = settings.ANSWER_CACHE_SIZE,
        ttl_seconds: int = settings.ANSWER_CACHE_TTL_SECONDS,
    ):
        """Initializes AnswerCache with parameters and lock."""
        self.enabled = enabled
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        # Structure: key -> ((answer_str, List[SourceItem]), timestamp)
        self._cache: OrderedDict[str, Tuple[Tuple[str, List[SourceItem]], float]] = OrderedDict()
        self._lock = threading.Lock()

        # Metrics
        self.hits = 0
        self.misses = 0

    @staticmethod
    def normalize_question(question: str) -> str:
        """Normalizes user question text for consistent lookup."""
        if not question:
            return ""
        text = question.strip().lower()
        text = re.sub(r'\s+', ' ', text)
        return text

    def get(self, question: str) -> Optional[Tuple[str, List[SourceItem]]]:
        """Retrieves cached (answer, sources) if present and unexpired."""
        if not self.enabled:
            return None

        key = self.normalize_question(question)
        if not key:
            return None

        with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None

            payload, timestamp = self._cache[key]
            if time.time() - timestamp > self.ttl_seconds:
                del self._cache[key]
                self.misses += 1
                return None

            self._cache.move_to_end(key)
            self.hits += 1
            return payload

    def put(self, question: str, answer: str, sources: List[SourceItem]) -> None:
        """Caches RAG answer and source citations."""
        if not self.enabled or not answer:
            return

        key = self.normalize_question(question)
        if not key:
            return

        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = ((answer, sources), time.time())

            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def clear(self) -> None:
        """Clears cached answers and resets metrics."""
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
                "answer_cache_enabled": self.enabled,
                "answer_cache_size": len(self._cache),
                "answer_cache_max_size": self.max_size,
                "answer_cache_hits": self.hits,
                "answer_cache_misses": self.misses,
                "answer_cache_hit_rate": round(hit_rate, 4),
            }


# Singleton answer cache instance
answer_cache = AnswerCache()
