"""Comprehensive verification script for Supabase PostgreSQL migration, API endpoints, prompt logging, health check, and RAG regression testing."""

import asyncio
from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from app.config import settings
from app.database.sqlite import SessionLocal
from app.knowledge.rag.answer_cache import answer_cache
from app.knowledge.rag.chat_service import ChatService
from app.knowledge.retrieval.query_embedding_cache import query_embedding_cache
from app.knowledge.retrieval.retrieval_pipeline import RetrievalPipeline
from app.main import app


def verify_api_endpoints():
    print("\n" + "=" * 90)
    print(" 🏥 STEP 10.1 — TESTING API ENDPOINTS & SUPABASE POSTGRESQL PROBE")
    print("=" * 90 + "\n")

    with TestClient(app) as client:
        # 1. Health Probe
        resp = client.get("/health")
        assert resp.status_code == 200, f"Health check failed: {resp.text}"
        health_data = resp.json()
        print("1. Health Endpoint /health:")
        print(f"   Status: {health_data.get('status')} | DB: {health_data.get('database')}\n")
        assert health_data.get("database") == "healthy"

        # 2. Join Team Endpoint
        team_payload = {
            "team_name": "TEAM-POSTGRES-TEST",
            "member_names": ["Pawan", "Rahul", "Kabilan"],
        }
        resp = client.post("/api/teams/join", json=team_payload)
        assert resp.status_code == 200, f"Join team failed: {resp.text}"
        team_data = resp.json()
        print("2. Join Team POST /api/teams/join:")
        print(f"   Team Name: {team_data.get('team_name')} | Members: {team_data.get('member_names')} | Started At: {team_data.get('started_at')}\n")

        # 3. Get Team Info Endpoint
        resp = client.get("/api/teams/TEAM-POSTGRES-TEST")
        assert resp.status_code == 200, f"Get team failed: {resp.text}"
        print("3. Get Team GET /api/teams/TEAM-POSTGRES-TEST:")
        print(f"   Retrieved Team: {resp.json().get('team_name')}\n")

        # 4. Prompt Logging & Retrieval Endpoint
        db = SessionLocal()
        try:
            from app.services.team_service import TeamService
            TeamService.log_prompt(
                db=db,
                team_name="TEAM-POSTGRES-TEST",
                prompt="Test prompt question",
                response="Test RAG response answer",
            )
        finally:
            db.close()

        resp = client.get("/api/teams/TEAM-POSTGRES-TEST/prompts")
        assert resp.status_code == 200, f"Get team prompts failed: {resp.text}"
        prompts_data = resp.json()
        print("4. Get Team Prompts GET /api/teams/TEAM-POSTGRES-TEST/prompts:")
        print(f"   Prompt Log Count: {len(prompts_data)} | Latest Prompt: '{prompts_data[-1].get('prompt')}'\n")
        assert len(prompts_data) >= 1


async def verify_rag_regression():
    print("=" * 90)
    print(" 🚀 STEP 11 — RAG REGRESSION TEST & LATENCY BREAKDOWN (SUPABASE POSTGRESQL)")
    print("=" * 90 + "\n")

    # Clear caches to measure uncached baseline
    query_embedding_cache.clear()
    answer_cache.clear()

    pipeline = RetrievalPipeline()
    chat_service = ChatService(retrieval_pipeline=pipeline)

    questions = [
        "What was the company's revenue in FY2025-26?",
        "Compare the company's revenue, profit after tax and EPS between FY2024-25 and FY2025-26.",
        "Who are the current owners of the company and what does the annual report say about its marketing strategies?",
    ]

    for idx, q in enumerate(questions, 1):
        print("-" * 90)
        print(f" QUESTION {idx}: '{q}'")
        print("-" * 90)

        t_start = time.perf_counter()
        res = await chat_service.ask_async(q)
        t_end = time.perf_counter()

        print(f"Generated Answer:\n{res.answer}\n")
        print(f"Sources Cited: {len(res.sources)}")
        print(f"Total Execution Time: {(t_end - t_start):.3f}s\n")

        assert len(res.answer.strip()) > 5, "Answer generated is too short or empty!"
        assert len(res.sources) > 0, "No sources cited!"

    print("=" * 90)
    print(" ✅ ALL API ENDPOINTS & RAG REGRESSION TESTS PASSED CLEANLY WITH SUPABASE POSTGRESQL!")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    verify_api_endpoints()
    asyncio.run(verify_rag_regression())
