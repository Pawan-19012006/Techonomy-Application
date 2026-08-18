"""Real LLM Provider Credential & Connectivity Validation Test Suite.

These tests execute against live external APIs (Gemini & OpenRouter/Nemotron) when valid credentials
are configured in environment variables.

Commands:
  Local Venv:   PYTHONPATH=. .venv/bin/python -m pytest tests/test_real_providers.py -v
  Docker Stack: docker compose exec backend python -m pytest tests/test_real_providers.py -v
"""

import asyncio
import os
import pytest

from app.config import settings
from app.database.db import SessionLocal
from app.database.models import LLMLaneModel
from app.knowledge.rag.llm_gateway import LLMGateway
from app.knowledge.rag.providers import GeminiProviderAdapter, NemotronProviderAdapter
from app.knowledge.rag.scheduler import QuotaScheduler


def _get_valid_key(env_var_name: str) -> str:
    """Helper returning clean API key from environment or app.config settings if set and not placeholder."""
    val = os.getenv(env_var_name, "").strip()
    if not val and hasattr(settings, env_var_name):
        val = str(getattr(settings, env_var_name, "")).strip()
    if not val or "your-" in val.lower() or "here" in val.lower():
        return ""
    return val


def test_real_gemini_connectivity():
    """Verify live Gemini API connection using GeminiProviderAdapter."""
    api_key = _get_valid_key("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY environment variable is not configured with a valid key.")

    async def _run():
        adapter = GeminiProviderAdapter()
        prompt = "Respond with exactly one word: OK"

        response = await adapter.generate_async(
            prompt=prompt,
            model=settings.GEMINI_MODEL,
            api_key=api_key,
            max_tokens=10,
        )

        assert response is not None
        assert len(response.strip()) > 0
        assert api_key not in response

    asyncio.run(_run())


def test_real_openrouter_connectivity():
    """Verify live OpenRouter/Nemotron API connection using NemotronProviderAdapter."""
    api_key = _get_valid_key("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY environment variable is not configured with a valid key.")

    async def _run():
        adapter = NemotronProviderAdapter(base_url=settings.OPENROUTER_BASE_URL)
        prompt = "Respond with exactly one word: OK"

        response = await adapter.generate_async(
            prompt=prompt,
            model=settings.PRIMARY_MODEL,
            api_key=api_key,
            max_tokens=10,
        )

        assert response is not None
        assert len(response.strip()) > 0
        assert api_key not in response

    asyncio.run(_run())


def test_real_gemini_streaming():
    """Verify real streaming response via LLMGateway.generate_stream_async."""
    api_key = _get_valid_key("OPENROUTER_API_KEY") or _get_valid_key("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("No valid LLM API key configured for streaming validation.")

    async def _run():
        gateway = LLMGateway()
        prompt = "Count 1 to 3."

        chunks = []
        async for token in gateway.generate_stream_async(prompt):
            chunks.append(token)

        assert len(chunks) > 0
        full_output = "".join(chunks)
        assert len(full_output.strip()) > 0
        assert api_key not in full_output

    asyncio.run(_run())


def test_real_gateway_gemini_primary_path():
    """Verify routing a real request through LLMGateway selects Gemini when eligible."""
    gemini_key = _get_valid_key("GEMINI_API_KEY")
    if not gemini_key:
        pytest.skip("GEMINI_API_KEY environment variable is not configured.")

    async def _run():
        gateway = LLMGateway()
        prompt = "Hello"

        response = await gateway.generate_async(prompt)

        assert response is not None
        assert len(response.strip()) > 0

        # Verify PostgreSQL DB state
        db = SessionLocal()
        try:
            gemini_lanes = db.query(LLMLaneModel).filter(LLMLaneModel.provider == "gemini").all()
            assert len(gemini_lanes) > 0
            total_used = sum(l.requests_used for l in gemini_lanes)
            assert total_used > 0
            active_count = sum(l.active_requests for l in gemini_lanes)
            assert active_count == 0
            for l in gemini_lanes:
                assert "GEMINI_API_KEY" in l.credential_ref
                assert gemini_key not in l.credential_ref
        finally:
            db.close()

    asyncio.run(_run())


def test_real_fallback_path():
    """Verify gateway falls back to OpenRouter/Nemotron when all Gemini lanes are unavailable."""
    openrouter_key = _get_valid_key("OPENROUTER_API_KEY")
    if not openrouter_key:
        pytest.skip("OPENROUTER_API_KEY environment variable is not configured for fallback test.")

    async def _run():
        db = SessionLocal()
        original_states = {}
        try:
            # Mark all Gemini lanes as DAILY_EXHAUSTED temporarily
            gemini_rows = db.query(LLMLaneModel).filter(LLMLaneModel.provider == "gemini").all()
            for row in gemini_rows:
                original_states[row.lane_id] = (row.state, row.requests_used)
                row.state = "DAILY_EXHAUSTED"
                row.requests_used = row.daily_limit
            db.commit()

            gateway = LLMGateway()
            prompt = "Hello fallback"

            response = await gateway.generate_async(prompt)

            assert response is not None
            assert len(response.strip()) > 0

            # Verify fallback lane updated
            nemotron_rows = db.query(LLMLaneModel).filter(LLMLaneModel.provider == "nemotron").all()
            total_nemotron_used = sum(r.requests_used for r in nemotron_rows)
            assert total_nemotron_used > 0
            for r in nemotron_rows:
                assert "OPENROUTER_API_KEY" in r.credential_ref
                assert openrouter_key not in r.credential_ref

        finally:
            # Restore original database state
            db.rollback()
            for lane_id, (state, used) in original_states.items():
                row = db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == lane_id).first()
                if row:
                    row.state = state
                    row.requests_used = used
            db.commit()
            db.close()

    asyncio.run(_run())


def test_credential_privacy_across_system():
    """Verify raw API keys are never stored in DB, scheduler status, or string representations."""
    gemini_key = _get_valid_key("GEMINI_API_KEY")
    openrouter_key = _get_valid_key("OPENROUTER_API_KEY")

    keys_to_check = [k for k in [gemini_key, openrouter_key] if k]

    if not keys_to_check:
        pytest.skip("No API keys present in environment to verify privacy.")

    db = SessionLocal()
    try:
        lane_rows = db.query(LLMLaneModel).all()
        for row in lane_rows:
            for key in keys_to_check:
                assert key not in str(row.lane_id)
                assert key not in str(row.provider)
                assert key not in str(row.credential_ref)
                assert key not in str(row.model)

        scheduler = QuotaScheduler(
            gemini_api_key=gemini_key if gemini_key else "dummy_key",
            nemotron_api_key=openrouter_key if openrouter_key else "dummy_key",
        )
        status_dict = scheduler.get_status()
        status_str = str(status_dict)

        for key in keys_to_check:
            assert key not in status_str, f"Raw API key found in scheduler.get_status() output!"
    finally:
        db.close()
