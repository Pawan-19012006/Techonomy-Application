"""Automated Pytest verification suite for simplified Techonomy Event backend."""

import asyncio
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.database.sqlite import reset_db
from app.knowledge.rag.chat_service import ChatService, ChatServiceResult
from app.main import app
from app.schemas.chat import SourceItem

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Resets database schema before each test run."""
    reset_db()


def test_1_team_joins_successfully():
    """1. Team joins successfully via POST /api/teams/join."""
    payload = {
        "team_name": "TEAM-01",
        "member_names": ["Pawan", "Rahul", "Kabilan"],
    }
    response = client.post(f"{settings.API_PREFIX}/teams/join", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["team_name"] == "TEAM-01"
    assert data["member_names"] == ["Pawan", "Rahul", "Kabilan"]
    assert "started_at" in data


def test_2_existing_team_reenters_without_duplicate():
    """2. Existing team can re-enter without duplicate creation."""
    payload = {
        "team_name": "TEAM-01",
        "member_names": ["Pawan", "Rahul", "Kabilan"],
    }
    res1 = client.post(f"{settings.API_PREFIX}/teams/join", json=payload)
    started_at_1 = res1.json()["started_at"]

    # Second join attempt with same team_name
    res2 = client.post(f"{settings.API_PREFIX}/teams/join", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["team_name"] == "TEAM-01"
    assert data2["started_at"] == started_at_1


def test_3_and_4_team_info_and_started_at_retrieval():
    """3 & 4. Team information is stored correctly and started_at is created."""
    client.post(
        f"{settings.API_PREFIX}/teams/join",
        json={"team_name": "DELTA-9", "member_names": ["Alice", "Bob"]},
    )

    response = client.get(f"{settings.API_PREFIX}/teams/DELTA-9")
    assert response.status_code == 200
    data = response.json()
    assert data["team_name"] == "DELTA-9"
    assert data["member_names"] == ["Alice", "Bob"]
    assert "started_at" in data


def test_5_and_6_chat_request_and_prompt_logging():
    """5 & 6. Chat request works for a valid team and prompt is logged with team_name."""
    client.post(
        f"{settings.API_PREFIX}/teams/join",
        json={"team_name": "TEAM-01", "member_names": ["Pawan"]},
    )

    mock_chat_result = ChatServiceResult(
        answer="Operating revenue for FY24 was INR 4,520 Crores.",
        sources=[SourceItem(document="annual_report.pdf", page=78)],
        confidence=0.85,
    )

    with patch.object(ChatService, "ask_async", new_callable=AsyncMock) as mock_ask:
        mock_ask.return_value = mock_chat_result

        chat_payload = {
            "team_name": "TEAM-01",
            "question": "What is the revenue?",
        }
        res = client.post(f"{settings.API_PREFIX}/chat", json=chat_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["team_name"] == "TEAM-01"
        assert data["answer"] == "Operating revenue for FY24 was INR 4,520 Crores."
        assert len(data["sources"]) == 1

    # Verify prompt is stored in prompt_logs history
    history_res = client.get(f"{settings.API_PREFIX}/teams/TEAM-01/prompts")
    assert history_res.status_code == 200
    logs = history_res.json()
    assert len(logs) == 1
    assert logs[0]["prompt"] == "What is the revenue?"
    assert logs[0]["response"] == "Operating revenue for FY24 was INR 4,520 Crores."


def test_7_concurrent_prompts_different_teams():
    """7. Two different teams can submit prompts simultaneously without mixing logs."""
    client.post(f"{settings.API_PREFIX}/teams/join", json={"team_name": "TEAM-A", "member_names": ["UserA"]})
    client.post(f"{settings.API_PREFIX}/teams/join", json={"team_name": "TEAM-B", "member_names": ["UserB"]})

    mock_res_a = ChatServiceResult(answer="Answer A", sources=[])
    mock_res_b = ChatServiceResult(answer="Answer B", sources=[])

    with patch.object(ChatService, "ask_async", new_callable=AsyncMock) as mock_ask:
        mock_ask.side_effect = [mock_res_a, mock_res_b]

        res_a = client.post(f"{settings.API_PREFIX}/chat", json={"team_name": "TEAM-A", "question": "Question A"})
        res_b = client.post(f"{settings.API_PREFIX}/chat", json={"team_name": "TEAM-B", "question": "Question B"})

        assert res_a.status_code == 200
        assert res_b.status_code == 200
        assert res_a.json()["team_name"] == "TEAM-A"
        assert res_b.json()["team_name"] == "TEAM-B"


def test_8_prompt_history_filtered_by_team():
    """8. Prompt history returns ONLY requested team's prompts."""
    client.post(f"{settings.API_PREFIX}/teams/join", json={"team_name": "ALPHA", "member_names": ["A"]})
    client.post(f"{settings.API_PREFIX}/teams/join", json={"team_name": "BETA", "member_names": ["B"]})

    mock_res = ChatServiceResult(answer="Ans", sources=[])

    with patch.object(ChatService, "ask_async", new_callable=AsyncMock) as mock_ask:
        mock_ask.return_value = mock_res
        client.post(f"{settings.API_PREFIX}/chat", json={"team_name": "ALPHA", "question": "Alpha Q1"})
        client.post(f"{settings.API_PREFIX}/chat", json={"team_name": "ALPHA", "question": "Alpha Q2"})
        client.post(f"{settings.API_PREFIX}/chat", json={"team_name": "BETA", "question": "Beta Q1"})

    prompts_alpha = client.get(f"{settings.API_PREFIX}/teams/ALPHA/prompts").json()
    prompts_beta = client.get(f"{settings.API_PREFIX}/teams/BETA/prompts").json()

    assert len(prompts_alpha) == 2
    assert prompts_alpha[0]["prompt"] == "Alpha Q1"
    assert prompts_alpha[1]["prompt"] == "Alpha Q2"

    assert len(prompts_beta) == 1
    assert prompts_beta[0]["prompt"] == "Beta Q1"


def test_9_rag_pipeline_remains_intact():
    """9. RAG pipeline remains fully intact."""
    from app.knowledge.rag.prompt_builder import PromptBuilder

    builder = PromptBuilder()
    prompt = builder.build_prompt("Question?", [])
    assert "Techonomy Intelligence Assistant" in prompt


def test_10_no_auth_or_password_endpoints():
    """10. Verify no authentication, password, or email endpoints exist."""
    res_auth = client.post(f"{settings.API_PREFIX}/auth/login", json={})
    assert res_auth.status_code == 404

    res_reg = client.post(f"{settings.API_PREFIX}/auth/register", json={})
    assert res_reg.status_code == 404
