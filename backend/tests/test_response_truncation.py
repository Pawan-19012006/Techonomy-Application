"""Targeted tests for response truncation, finish reason detection, and long streaming/non-streaming response generation."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.config import settings
from app.knowledge.rag.llm_gateway import LLMGateway
from app.knowledge.rag.providers import GeminiProviderAdapter, NemotronProviderAdapter, extract_clean_answer


def _get_valid_key(env_var_name: str) -> str:
    """Helper returning configured API key from settings."""
    return getattr(settings, env_var_name, "") or ""


# ==============================================================================
# Test 1 — Long non-streaming response
# ==============================================================================
def test_long_non_streaming_response():
    """Verify that non-streaming LLM generation handles long prompts and returns complete answers."""
    async def _run():
        gateway = LLMGateway(max_tokens=2048)
        prompt = (
            "Write a detailed 10-item financial summary covering Revenue, Profit After Tax, "
            "EBITDA, Net Worth, Debt-to-Equity, Cash Flow, ROE, Operating Margin, EPS, and Capex."
        )

        response = await gateway.generate_async(prompt)
        assert response is not None
        assert len(response.strip()) > 100
        assert not response.endswith("- Volume growth of")
    asyncio.run(_run())


# ==============================================================================
# Test 2 — Long streaming response
# ==============================================================================
def test_long_streaming_response():
    """Verify that streaming generation yields multiple chunks, accumulates cleanly, and completes without truncation."""
    async def _run():
        gateway = LLMGateway(max_tokens=2048)
        prompt = "Provide a comprehensive 5-bullet summary of corporate governance policies with detailed explanations."

        chunks = []
        async for chunk in gateway.generate_stream_async(prompt):
            chunks.append(chunk)

        full_response = "".join(chunks)
        assert len(chunks) >= 1
        assert len(full_response.strip()) > 50
        assert "Prompt cannot be empty" not in full_response
    asyncio.run(_run())


# ==============================================================================
# Test 3 — SSE chunk accumulation & non-destructive contract
# ==============================================================================
def test_sse_chunk_accumulation_contract():
    """Verify SSE streaming contract yields non-destructive chunks that concatenate into complete response."""
    async def _run():
        mock_gemini = MagicMock()
        async def mock_stream(*args, **kwargs):
            yield ("Hello ", None)
            yield ("world! ", None)
            yield ("This is ", None)
            yield ("a complete response.", "STOP")

        mock_gemini.generate_stream_async = mock_stream

        gateway = LLMGateway(gemini_adapter=mock_gemini)
        accumulated = []
        async for token in gateway.generate_stream_async("Test prompt"):
            accumulated.append(token)

        final_text = "".join(accumulated)
        assert final_text == "Hello world! This is a complete response."
        assert len(accumulated) == 4
    asyncio.run(_run())


# ==============================================================================
# Test 4 — Finish reason detection & truncation notices
# ==============================================================================
def test_finish_reason_max_tokens_handling():
    """Verify that finish_reason MAX_TOKENS / length is captured in metrics and appends a notice via LLMGateway."""
    # Gemini MAX_TOKENS finish reason
    gemini_adapter = GeminiProviderAdapter()
    gemini_data = {
        "candidates": [
            {
                "content": {"parts": [{"text": "Partial revenue response cut off at item 5."}]},
                "finishReason": "MAX_TOKENS",
            }
        ]
    }
    gemini_text, finish_reason = gemini_adapter._extract_gemini_text(gemini_data, max_tokens=500)
    assert finish_reason == "MAX_TOKENS"
    assert "Output reached configured token limit of 500" in gemini_text

    # OpenRouter length finish reason
    openrouter_data = {
        "choices": [
            {
                "message": {"content": "Partial profit response cut off at item 3."},
                "finish_reason": "length",
            }
        ]
    }
    or_text, metrics = extract_clean_answer(openrouter_data, max_tokens=500)
    assert metrics["finish_reason"] == "length"
    assert or_text == "Partial profit response cut off at item 3."

    # Verify LLMGateway streaming truncation notice
    async def _run():
        mock_gemini = MagicMock()
        async def mock_stream(*args, **kwargs):
            yield ("Partial text...", "MAX_TOKENS")

        mock_gemini.generate_stream_async = mock_stream
        mock_gemini.generate_async = AsyncMock(return_value="Partial text...")
        mock_gemini.generate = MagicMock(return_value="Partial text...")

        gateway = LLMGateway(gemini_adapter=mock_gemini, max_tokens=500)
        accumulated = []
        async for token in gateway.generate_stream_async("Test prompt"):
            accumulated.append(token)

        final_text = "".join(accumulated)
        assert "Output reached configured token limit of 500" in final_text

    asyncio.run(_run())


# ==============================================================================
# Test 5 — Real provider long execution
# ==============================================================================
def test_real_provider_long_response():
    """Verify live Gemini and OpenRouter providers return complete answers for long prompts."""
    gemini_key = _get_valid_key("GEMINI_API_KEY")
    if not gemini_key:
        pytest.skip("GEMINI_API_KEY environment variable is not configured.")

    async def _run():
        gateway = LLMGateway(max_tokens=2048)
        prompt = (
            "List 5 major financial indicators for a manufacturing company. "
            "Provide a brief definition for each indicator."
        )

        response = await gateway.generate_async(prompt)
        assert response is not None
        assert len(response.strip()) > 150

        streamed_chunks = []
        async for chunk in gateway.generate_stream_async(prompt):
            streamed_chunks.append(chunk)

        streamed_text = "".join(streamed_chunks)
        assert len(streamed_text.strip()) > 150

    asyncio.run(_run())
