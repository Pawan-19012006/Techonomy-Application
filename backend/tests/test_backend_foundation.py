"""Pytest verification suite for Techonomy backend foundation APIs."""

import pytest
from fastapi.testclient import TestClient

from app.database.sqlite import init_db
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Ensures database tables exist before each test."""
    init_db()


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "healthy"


def test_auth_and_team_flow():
    # Register Team
    register_payload = {
        "name": "Beta Corp",
        "email": "beta@corp.com",
        "password": "SecurePassword123!",
        "question_limit": 2,
        "is_admin": False
    }
    res = client.post("/api/auth/register", json=register_payload)
    assert res.status_code == 201

    # Login
    login_payload = {"email": "beta@corp.com", "password": "SecurePassword123!"}
    res = client.post("/api/auth/login", json=login_payload)
    assert res.status_code == 200
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get Profile & Usage
    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == "beta@corp.com"

    res = client.get("/api/teams/usage", headers=headers)
    assert res.status_code == 200
    assert res.json()["remaining_questions"] == 2


def test_rate_limiter():
    # Register & Login
    reg_res = client.post("/api/auth/register", json={
        "name": "Limit Test Team",
        "email": "limit@test.com",
        "password": "Password123!",
        "question_limit": 1,
        "is_admin": False
    })
    assert reg_res.status_code == 201

    res = client.post("/api/auth/login", json={"email": "limit@test.com", "password": "Password123!"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # First Query (Allowed)
    res1 = client.post("/api/chat/query", json={"query": "Hello"}, headers=headers)
    assert res1.status_code == 200

    # Second Query (Rejected 429)
    res2 = client.post("/api/chat/query", json={"query": "Hello 2"}, headers=headers)
    assert res2.status_code == 429
