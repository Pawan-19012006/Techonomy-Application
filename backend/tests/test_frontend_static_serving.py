"""Unit tests for FastAPI production frontend static file serving and SPA fallback routing."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Returns a TestClient instance for testing app endpoints."""
    with TestClient(app) as c:
        yield c


def test_api_status_endpoint(client):
    """Verifies GET /api/status returns JSON status."""
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert "version" in data


def test_health_endpoint_accessibility(client):
    """Verifies GET /health returns 200 JSON and is not intercepted by SPA fallback."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("application/json")
    data = res.json()
    assert "status" in data
    assert "database" in data


def test_api_nonexistent_route_returns_404_json(client):
    """Verifies unmatched /api/* routes return 404 JSON, not HTML index fallback."""
    res = client.get("/api/nonexistent_route_12345")
    assert res.status_code == 404
    assert res.headers["content-type"].startswith("application/json")
    data = res.json()
    assert "detail" in data
    assert data["detail"] == "API endpoint not found" or data["detail"] == "Not Found"


def test_spa_client_side_route_fallback(client):
    """Verifies client-side SPA routes (/login, /dashboard) serve frontend or fallback."""
    for path in ["/", "/login", "/dashboard", "/teams"]:
        res = client.get(path)
        assert res.status_code == 200
        # If frontend/dist/index.html is present, content-type is text/html
        content_type = res.headers.get("content-type", "")
        if "text/html" in content_type:
            assert "<!DOCTYPE html>" in res.text or "<html" in res.text or "<script" in res.text
        else:
            assert res.json().get("status") == "online"
