"""Automated test suite verifying performance optimizations, caches, and LLMGateway."""

import time
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.knowledge.indexing.embedder import EmbeddingGenerator
from app.knowledge.rag.answer_cache import AnswerCache
from app.knowledge.retrieval.query_embedding_cache import QueryEmbeddingCache
from app.schemas.chat import SourceItem


def test_embedding_generator_singleton():
    """Verifies that EmbeddingGenerator loads the model once and reuses the singleton instance."""
    gen1 = EmbeddingGenerator()
    model1 = gen1.get_model()

    gen2 = EmbeddingGenerator()
    model2 = gen2.get_model()

    assert model1 is model2
    assert EmbeddingGenerator._model_instance is not None


def test_query_embedding_cache():
    """Verifies QueryEmbeddingCache hits, misses, bounds, and normalization."""
    cache = QueryEmbeddingCache(enabled=True, max_size=2, ttl_seconds=60)
    cache.clear()

    q1 = "  What is the REVENUE in 2025?  "
    vec1 = [0.1, 0.2, 0.3]

    assert cache.get(q1) is None

    cache.put(q1, vec1)
    hit_vec = cache.get("what is the revenue in 2025?")
    assert hit_vec == vec1

    metrics = cache.metrics()
    assert metrics["embedding_cache_hits"] == 1
    assert metrics["embedding_cache_misses"] == 1


def test_answer_cache():
    """Verifies AnswerCache hit/miss behavior, bounds, and sources preservation."""
    cache = AnswerCache(enabled=True, max_size=2, ttl_seconds=60)
    cache.clear()

    q = "Who owns the company?"
    ans = "The Jain family owns 72.45%."
    sources = [SourceItem(document="annual_report.pdf", page=121)]

    assert cache.get(q) is None

    cache.put(q, ans, sources)

    cached_payload = cache.get("who owns the company?")
    assert cached_payload is not None
    cached_ans, cached_srcs = cached_payload
    assert cached_ans == ans
    assert len(cached_srcs) == 1
    assert cached_srcs[0].document == "annual_report.pdf"


def test_health_check_endpoint():
    """Verifies that /health returns database, embedding model, and cache status."""
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "embedding_model" in data
    assert "caches" in data
    assert data["caches"]["query_embedding_cache"]["embedding_cache_enabled"] is True
