"""Dedicated Unit Test Suite for Production Latency Observability (Phase 4B).

Verifies:
1. Request correlation IDs (generated & preserved from X-Request-ID).
2. RAG stage timing instrumentation (Embedding, Qdrant, TTFT, Total LLM Generation).
3. Safe provider and fallback metadata capture.
4. Sanitized error tracebacks and total redaction of API keys.
5. Preserved SSE streaming token delivery and ChatResponse payloads.
6. Non-breaking resilience when logging encounters unexpected exceptions.
"""

import asyncio
import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.utils.observability import (
    LatencyTracker,
    generate_request_id,
    get_request_id,
    log_structured_event,
    sanitize_error_message,
    set_request_id,
)

client = TestClient(app)


def test_request_id_generated_and_preserved():
    """Verifies server generates req_ ID when header is missing, and preserves X-Request-ID when provided."""
    # 1. Custom request ID passed via header
    custom_id = "test_req_abc123"
    res1 = client.get("/", headers={"X-Request-ID": custom_id})
    assert res1.status_code == 200
    assert res1.headers.get("X-Request-ID") == custom_id

    # 2. No header provided -> server generates req_... ID
    res2 = client.get("/")
    assert res2.status_code == 200
    generated_id = res2.headers.get("X-Request-ID")
    assert generated_id is not None
    assert generated_id.startswith("req_")


def test_latency_tracker_stage_recording():
    """Verifies LatencyTracker accurately records stage durations and metrics."""
    tracker = LatencyTracker(request_id="req_test_tracker_123")
    
    tracker.record_db_team_lookup(12.5)
    tracker.record_db_quota_reservation(8.2, reserved=True)
    tracker.record_embedding(145.0)
    tracker.record_qdrant(65.3, chunk_count=5, succeeded=True, zero_results=False)
    tracker.record_llm_first_token(620.0)
    tracker.record_llm_complete(
        total_duration_ms=1850.0,
        provider="gemini",
        model="gemini-flash-lite-latest",
        fallback=False,
        chunk_count=24,
        finish_reason="STOP",
        stream_duration_ms=1230.0,
    )

    assert tracker.db_team_lookup_ms == 12.5
    assert tracker.db_quota_reservation_ms == 8.2
    assert tracker.embedding_ms == 145.0
    assert tracker.qdrant_ms == 65.3
    assert tracker.qdrant_chunks_retrieved == 5
    assert tracker.llm_ttft_ms == 620.0
    assert tracker.llm_total_duration_ms == 1850.0
    assert tracker.llm_provider == "gemini"
    assert tracker.llm_model == "gemini-flash-lite-latest"
    assert tracker.llm_fallback is False
    assert tracker.llm_finish_reason == "STOP"


def test_api_keys_never_appear_in_instrumentation_logs(caplog):
    """Verifies that API keys are strictly sanitized and never appear in structured logs or tracebacks."""
    sensitive_gemini = settings.GEMINI_API_KEY or "secret_gemini_key_99999"
    sensitive_openrouter = settings.OPENROUTER_API_KEY or "secret_openrouter_key_88888"

    with caplog.at_level(logging.INFO):
        log_structured_event(
            "TEST_EVENT",
            request_id="req_sanitize_test",
            gemini_key=sensitive_gemini,
            openrouter_key=sensitive_openrouter,
        )

        sanitized_msg = sanitize_error_message(f"Failed HTTP call with key {sensitive_gemini}")

    log_text = caplog.text
    if len(sensitive_gemini) > 4:
        assert sensitive_gemini not in log_text
    if len(sensitive_openrouter) > 4:
        assert sensitive_openrouter not in log_text

    assert "[REDACTED_API_KEY]" in sanitized_msg


def test_llm_gateway_ttft_and_streaming_latency_instrumentation(caplog):
    """Verifies LLMGateway captures TTFT on first token and total generation time during streaming."""
    from app.knowledge.rag.llm_gateway import LLMGateway

    async def run_test():
        mock_lane = MagicMock()
        mock_lane.provider = "gemini"
        mock_lane.lane_id = "lane-gemini-1"
        mock_lane.model = "gemini-flash-lite-latest"
        mock_lane.active_requests = 1
        mock_lane.requests_remaining = 14

        mock_scheduler = AsyncMock()
        mock_scheduler.select_lane_async.return_value = (mock_lane, "dummy_key", False)
        mock_scheduler.release_lane = MagicMock()

        async def mock_stream_gen(*args, **kwargs):
            yield "Hello", None
            yield " world!", "STOP"

        mock_adapter = MagicMock()
        mock_adapter.generate_stream_async = mock_stream_gen

        gateway = LLMGateway(scheduler=mock_scheduler, gemini_adapter=mock_adapter)
        tracker = LatencyTracker(request_id="req_stream_test")

        tokens = []
        with caplog.at_level(logging.INFO):
            async for chunk in gateway.generate_stream_async("Test query prompt", request_id="req_stream_test", tracker=tracker):
                tokens.append(chunk)

        assert "".join(tokens) == "Hello world!"
        assert tracker.llm_ttft_ms is not None
        assert tracker.llm_ttft_ms >= 0.0
        assert tracker.llm_total_duration_ms is not None
        assert tracker.llm_provider == "gemini"

    asyncio.run(run_test())

    log_text = caplog.text
    assert "[LLM_FIRST_TOKEN]" in log_text
    assert "[LLM_STREAM_COMPLETE]" in log_text


def test_sse_streaming_endpoint_preserves_contract_and_emits_latency(caplog):
    """Verifies /api/chat/stream SSE streaming format and latency summary emission."""
    mock_chat_result = MagicMock()
    mock_chat_result.answer = "Test answer"
    mock_chat_result.sources = []

    async def mock_gateway_stream(*args, **kwargs):
        yield "Token1 "
        yield "Token2"

    with patch("app.api.chat.LLMGateway.generate_stream_async", side_effect=mock_gateway_stream), \
         patch("app.knowledge.retrieval.retrieval_pipeline.RetrievalPipeline.retrieve") as mock_retrieve, \
         caplog.at_level(logging.INFO):

        mock_retrieve.return_value = MagicMock(reranked_results=[])

        payload = {"team_name": "OBS_TEAM", "question": "What is the event schedule?"}
        response = client.post("/api/chat/stream", json=payload, headers={"X-Request-ID": "req_sse_test_999"})

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        assert response.headers.get("X-Request-ID") == "req_sse_test_999"

        body = response.text
        assert "data: {\"token\": \"Token1 \"}" in body
        assert "data: {\"token\": \"Token2\"}" in body
        assert "data: {\"done\": true" in body

    log_text = caplog.text
    assert "[RAG_LATENCY_SUMMARY]" in log_text


def test_instrumentation_resilience_on_logging_error():
    """Verifies that an unexpected exception inside log_structured_event does not fail execution."""
    with patch("app.utils.observability.logger.info", side_effect=Exception("Disk full / logger error")):
        # Should not raise exception
        log_structured_event("FAULTY_EVENT", request_id="req_fault_123", test_param="val")

    tracker = LatencyTracker(request_id="req_fault_123")
    with patch("app.utils.observability.logger.info", side_effect=Exception("Disk full / logger error")):
        # Summary should handle error gracefully without raising
        tracker.emit_summary()
