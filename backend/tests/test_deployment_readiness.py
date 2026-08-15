"""Deployment Readiness & Health Check Unit Test Suite."""

import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

from app.config import Settings
from app.main import app


def test_cors_origins_parsing_comma_separated():
    """Verify CORS_ORIGINS parses comma-separated LAN IP URLs."""
    s = Settings(CORS_ORIGINS="http://localhost:3000,http://192.168.1.100:3000,http://10.0.0.5:5173")
    origins = s.cors_origins_list
    assert "http://localhost:3000" in origins
    assert "http://192.168.1.100:3000" in origins
    assert "http://10.0.0.5:5173" in origins
    assert len(origins) == 3


def test_cors_origins_parsing_json_array():
    """Verify CORS_ORIGINS parses JSON array strings."""
    s = Settings(CORS_ORIGINS='["http://localhost:3000", "http://192.168.1.100:3000"]')
    origins = s.cors_origins_list
    assert origins == ["http://localhost:3000", "http://192.168.1.100:3000"]


def test_cors_origins_empty_string_fallback():
    """Verify empty CORS_ORIGINS falls back to default localhost origins."""
    s = Settings(CORS_ORIGINS="")
    origins = s.cors_origins_list
    assert "http://localhost:3000" in origins
    assert "http://127.0.0.1:3000" in origins


def test_health_endpoint_response_structure():
    """Verify /health endpoint returns required deployment health fields without exposing API secrets."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert "backend" in data
    assert data["backend"] == "healthy"
    assert "database" in data
    assert "qdrant" in data
    assert "embedding_model" in data
    assert "caches" in data
    assert "version" in data

    # Verify credentials/secrets are not exposed in health response
    resp_text = response.text
    assert "OPENROUTER_API_KEY" not in resp_text
    assert "GEMINI_API_KEY" not in resp_text
    assert "sk-or-v1" not in resp_text


def test_preload_models_script_execution():
    """Verify scripts/preload_models.py executes cleanly and returns exit code 0."""
    from scripts.preload_models import main as preload_main
    exit_code = preload_main()
    assert exit_code == 0
