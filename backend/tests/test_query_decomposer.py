"""Unit tests for QueryDecomposer module."""

import pytest
from app.knowledge.retrieval.query_decomposer import QueryDecomposer


def test_single_intent_revenue():
    """Validates that a single financial question remains 1 query."""
    query = "What was the company's revenue in 2025?"
    subqueries = QueryDecomposer.decompose(query)
    assert len(subqueries) == 1
    assert subqueries[0] == query


def test_compound_ownership_and_marketing():
    """Validates that a compound query with distinct intents splits into 2 subqueries."""
    query = "Who are the current owners of the company and what are its marketing strategies?"
    subqueries = QueryDecomposer.decompose(query)
    assert len(subqueries) == 2
    assert "owners" in subqueries[0].lower()
    assert "marketing" in subqueries[1].lower()


def test_three_topic_list():
    """Validates that a multi-topic list query splits into 3 subqueries (max ceiling)."""
    query = "Tell me about ownership, marketing strategy and major products."
    subqueries = QueryDecomposer.decompose(query)
    assert len(subqueries) == 3
    assert any("ownership" in s.lower() for s in subqueries)
    assert any("marketing" in s.lower() for s in subqueries)
    assert any("product" in s.lower() for s in subqueries)


def test_related_financial_metrics_conservative():
    """Validates that related financial metrics ('revenue and profit') remain 1 query."""
    query = "What was revenue and profit in 2025?"
    subqueries = QueryDecomposer.decompose(query)
    assert len(subqueries) == 1
    assert subqueries[0] == query


def test_coherent_governance_topic_conservative():
    """Validates that coherent governance topic ('directors and responsibilities') remains 1 query."""
    query = "Who are the directors and what are their responsibilities?"
    subqueries = QueryDecomposer.decompose(query)
    assert len(subqueries) == 1
    assert subqueries[0] == query


def test_empty_query():
    """Validates empty query handling."""
    assert QueryDecomposer.decompose("") == [""]
    assert QueryDecomposer.decompose("   ") == ["   "]
