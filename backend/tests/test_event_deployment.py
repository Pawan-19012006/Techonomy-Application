"""Automated tests for event deployment portability, environment loading, SPA routing, and secret privacy."""

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.config import Settings, settings
from app.main import app


@pytest.fixture
def client():
    """Returns a TestClient instance for testing app endpoints."""
    with TestClient(app) as c:
        yield c


def test_environment_configuration_defaults():
    """Verifies Settings initializes clean defaults for key environment fields."""
    s = Settings()
    assert s.HOST == "0.0.0.0"
    assert s.PORT == 8000
    assert s.API_PREFIX == "/api"
    assert s.EMBEDDING_MODEL_NAME == "BAAI/bge-small-en-v1.5"


def test_tracked_files_contain_no_secrets():
    """Audits tracked configuration files to ensure zero real API keys are present."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    example_file = repo_root / "backend" / ".env.example"

    assert example_file.exists()
    content = example_file.read_text(encoding="utf-8")

    # Verify placeholders are present
    assert "your_gemini_api_key_here" in content
    assert "your_openrouter_api_key_here" in content
    assert "your_qdrant_cloud_api_key_here" in content

    # Verify no raw live keys are committed in example file
    assert "AIzaSy" not in content
    assert "sk-or-v1-" not in content


def test_api_status_and_health_endpoints(client):
    """Verifies /api/status and /health endpoints function correctly."""
    status_res = client.get("/api/status")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "online"

    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert "status" in health_res.json()


def test_spa_routing_and_api_protection(client):
    """Verifies SPA routes render index.html and /api/* routes enforce JSON 404 responses."""
    # SPA routes return 200 OK
    for path in ["/", "/login", "/dashboard"]:
        res = client.get(path)
        assert res.status_code == 200

    # Nonexistent API route returns 404 JSON, not HTML
    api_res = client.get("/api/nonexistent_test_route")
    assert api_res.status_code == 404
    assert api_res.headers["content-type"].startswith("application/json")
