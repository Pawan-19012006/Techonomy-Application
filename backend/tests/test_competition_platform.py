"""Comprehensive test suite for the Techonomy Competition Platform layer."""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from app.database.sqlite import reset_db
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Initializes clean database tables before running each test."""
    reset_db()


def test_health_endpoints():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "online"

    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["database"] == "healthy"


def test_competition_platform_full_flow():
    # 1. Register Admin & Team
    admin_payload = {
        "name": "Admin Operator",
        "email": "admin_comp@techonomy.com",
        "password": "AdminSecret123!",
        "question_limit": 100,
        "is_admin": True
    }
    res = client.post("/api/auth/register", json=admin_payload)
    assert res.status_code == 201

    team_payload = {
        "name": "Competition Team Alpha",
        "email": "alpha@competition.com",
        "password": "TeamPassword123!",
        "question_limit": 5,
        "is_admin": False
    }
    res = client.post("/api/auth/register", json=team_payload)
    assert res.status_code == 201

    # 2. Login
    admin_token = client.post("/api/auth/login", json={
        "email": "admin_comp@techonomy.com",
        "password": "AdminSecret123!"
    }).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    team_token = client.post("/api/auth/login", json={
        "email": "alpha@competition.com",
        "password": "TeamPassword123!"
    }).json()["access_token"]
    team_headers = {"Authorization": f"Bearer {team_token}"}

    # 3. Create Competition Event (Admin)
    now = datetime.now(timezone.utc)
    event_payload = {
        "name": "Techonomy Hackathon 2026",
        "description": "Annual enterprise AI knowledge intelligence competition",
        "business_objective": "Build high-speed enterprise QA solutions",
        "rules": "No unauthorized external API calls",
        "start_time": (now - timedelta(hours=1)).isoformat(),
        "end_time": (now + timedelta(hours=5)).isoformat(),
        "question_limit": 10,
        "is_active": True
    }
    res = client.post("/api/event", json=event_payload, headers=admin_headers)
    assert res.status_code == 201
    event_id = res.json()["id"]
    assert res.json()["status"] == "ACTIVE"

    # 4. Check GET /api/event & GET /api/event/status
    res = client.get("/api/event", headers=team_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Techonomy Hackathon 2026"

    res = client.get("/api/event/status", headers=team_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "ACTIVE"
    assert res.json()["started"] is True
    assert res.json()["timer_remaining_seconds"] > 0

    # 5. Check Document Upload & Delete
    file_data = b"Sample competition pdf document"
    files = {"file": ("guidelines.pdf", file_data, "application/pdf")}
    res = client.post("/api/documents/upload?pages=12", files=files, headers=team_headers)
    assert res.status_code == 201
    doc_id = res.json()["document"]["id"]
    assert res.json()["document"]["pages"] == 12

    res = client.get(f"/api/documents/{doc_id}", headers=team_headers)
    assert res.status_code == 200
    assert res.json()["filename"] == "guidelines.pdf"

    # 6. Check Unified Dashboard Endpoint (GET /api/dashboard)
    res = client.get("/api/dashboard", headers=team_headers)
    assert res.status_code == 200
    dash = res.json()
    assert dash["team_name"] == "Competition Team Alpha"
    assert dash["current_event"] == "Techonomy Hackathon 2026"
    assert dash["documents_available"] == 1
    assert dash["questions_remaining"] == 5

    # 7. Check Team Questions & Prompt History
    res = client.get("/api/teams/questions", headers=team_headers)
    assert res.status_code == 200
    assert res.json()["questions_remaining"] == 5

    # Submit 1 Chat query
    res = client.post("/api/chat/query", json={"query": "What are the competition rules?"}, headers=team_headers)
    assert res.status_code == 200

    res = client.get("/api/teams/history", headers=team_headers)
    assert res.status_code == 200
    assert res.json()["total_count"] == 1

    res = client.get("/api/history", headers=team_headers)
    assert res.status_code == 200
    assert res.json()["total_count"] == 1

    # 8. Check Admin Filtering and Analytics
    res = client.get("/api/admin/prompts", headers=admin_headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

    res = client.get("/api/admin/analytics", headers=admin_headers)
    assert res.status_code == 200
    analytics = res.json()
    assert analytics["total_teams"] >= 2
    assert analytics["total_prompts"] >= 1

    res = client.get("/api/admin/documents", headers=admin_headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

    res = client.get("/api/admin/event/status", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "ACTIVE"

    # 9. Delete Document
    res = client.delete(f"/api/documents/{doc_id}", headers=team_headers)
    assert res.status_code == 200

    # 10. Deactivate Event (Admin)
    res = client.patch(f"/api/event/{event_id}/deactivate", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "PAUSED"
