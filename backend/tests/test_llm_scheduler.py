"""Comprehensive unit test suite for Quota-Aware LLM Gateway & Scheduler (Phase 1 & Phase 2A)."""

import asyncio
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.database.models import LLMLaneModel
from app.database.db import SessionLocal, init_db
from app.knowledge.exceptions import LLMQuotaExhaustedError
from app.knowledge.rag.lane import LLMLane, LanePriority, LaneState
from app.knowledge.rag.llm_gateway import LLMGateway
from app.knowledge.rag.providers import LLMProvider
from app.knowledge.rag.scheduler import QuotaScheduler


@pytest.fixture(autouse=True)
def clean_db():
    """Ensures database tables are initialized and fresh before each test."""
    init_db()
    db = SessionLocal()
    try:
        db.query(LLMLaneModel).delete()
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture
def test_scheduler():
    """Returns a clean QuotaScheduler instance for testing."""
    return QuotaScheduler(
        gemini_api_key="mock-gemini-key",
        nemotron_api_key="mock-nemotron-key",
        gemini_enabled=True,
        nemotron_enabled=True,
        gemini_model="gemini-2.0-flash",
        nemotron_model="nvidia/nemotron-3.5-lightning:free",
        gemini_test_limit=3,
        nemotron_test_limit=3,
        gemini_max_concurrency=1,
        nemotron_max_concurrency=1,
        gemini_num_lanes=10,
        nemotron_num_lanes=10,
        cooldown_seconds=60.0,
    )


def test_1_gemini_selected_when_capacity_exists(test_scheduler):
    """1. Test Gemini primary lane is selected when Gemini capacity exists."""
    lane, api_key, is_fallback = test_scheduler.select_lane_sync()
    assert lane.provider == "gemini"
    assert lane.lane_id.startswith("G")
    assert is_fallback is False
    assert api_key == "mock-gemini-key"


def test_2_multiple_gemini_lanes_distribute_requests(test_scheduler):
    """2. Test multiple Gemini lanes distribute requests across the pool."""
    selected_lanes = []
    for _ in range(5):
        lane, _, _ = test_scheduler.select_lane_sync()
        selected_lanes.append(lane.lane_id)

    # Expect 5 distinct Gemini lanes chosen (G01..G05)
    assert len(set(selected_lanes)) == 5


def test_3_busy_gemini_lane_is_skipped(test_scheduler):
    """3. Test a busy Gemini lane (active_requests >= max_concurrency) is skipped."""
    lane1, _, _ = test_scheduler.select_lane_sync()
    assert lane1.lane_id == "G01"

    # Next selection must pick a non-busy lane (e.g. G02)
    lane2, _, _ = test_scheduler.select_lane_sync()
    assert lane2.lane_id != "G01"
    assert lane2.provider == "gemini"


def test_4_exhausted_gemini_lane_is_skipped(test_scheduler):
    """4. Test an exhausted Gemini lane (requests_used >= limit) is skipped."""
    db = SessionLocal()
    try:
        db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G01").update({
            LLMLaneModel.requests_used: 3,
            LLMLaneModel.state: LaneState.DAILY_EXHAUSTED.value,
        })
        db.commit()
    finally:
        db.close()
    test_scheduler._sync_db_lanes()

    selected, _, _ = test_scheduler.select_lane_sync()
    assert selected.lane_id != "G01"


def test_5_gemini_exhaustion_causes_nemotron_fallback(test_scheduler):
    """5. Test Gemini pool exhaustion causes fallback to Nemotron pool."""
    db = SessionLocal()
    try:
        db.query(LLMLaneModel).filter(LLMLaneModel.provider == "gemini").update({
            LLMLaneModel.requests_used: 3,
            LLMLaneModel.state: LaneState.DAILY_EXHAUSTED.value,
        })
        db.commit()
    finally:
        db.close()
    test_scheduler._sync_db_lanes()

    selected, api_key, is_fallback = test_scheduler.select_lane_sync()
    assert is_fallback is True
    assert selected.provider == "nemotron"
    assert selected.lane_id.startswith("N")
    assert api_key == "mock-nemotron-key"


def test_6_nemotron_not_used_while_gemini_has_capacity(test_scheduler):
    """6. Test Nemotron fallback is NEVER used while Gemini has available capacity."""
    for _ in range(3):
        lane, _, is_fallback = test_scheduler.select_lane_sync()
        assert is_fallback is False
        assert lane.provider == "gemini"


def test_7_both_pools_exhausted_raises_controlled_error(test_scheduler):
    """7. Test error raised when both Gemini and Nemotron pools are exhausted."""
    db = SessionLocal()
    try:
        db.query(LLMLaneModel).update({
            LLMLaneModel.requests_used: 3,
            LLMLaneModel.state: LaneState.DAILY_EXHAUSTED.value,
        })
        db.commit()
    finally:
        db.close()
    test_scheduler._sync_db_lanes()

    with pytest.raises(LLMQuotaExhaustedError):
        test_scheduler.select_lane_sync()


@pytest.mark.anyio
async def test_8_concurrent_acquisition_does_not_oversubscribe(test_scheduler):
    """8. Test concurrent lane selection under asyncio.Lock prevents oversubscription."""
    lanes = []

    async def worker():
        lane, _, _ = await test_scheduler.select_lane_async()
        lanes.append(lane.lane_id)

    await asyncio.gather(*[worker() for _ in range(10)])

    assert len(set(lanes)) == 10
    assert len(lanes) == 10


def test_9_successful_request_releases_active_capacity(test_scheduler):
    """9. Test releasing a lane slot decrements active_requests and restores AVAILABLE state."""
    lane, _, _ = test_scheduler.select_lane_sync()
    assert lane.active_requests == 1

    test_scheduler.release_lane(lane.lane_id, success=True)
    assert lane.active_requests == 0


def test_10_rate_limited_lane_enters_cooldown(test_scheduler):
    """10. Test 429 rate-limited lane enters RATE_LIMITED state and is skipped during cooldown."""
    lane, _, _ = test_scheduler.select_lane_sync()
    test_scheduler.release_lane(lane.lane_id, success=False, status_code=429)

    assert lane.state == LaneState.RATE_LIMITED
    assert lane.cooldown_until is not None
    assert lane.is_eligible() is False


def test_11_transient_provider_failure_does_not_destroy_lane(test_scheduler):
    """11. Test transient single error increases error_count but leaves lane eligible."""
    lane, _, _ = test_scheduler.select_lane_sync()
    test_scheduler.release_lane(lane.lane_id, success=False, status_code=500, error=Exception("Internal Server Error"))

    assert lane.error_count == 1
    assert lane.is_eligible() is True


def test_12_usage_counters_update_correctly(test_scheduler):
    """12. Test requests_used and requests_remaining update accurately."""
    lane = test_scheduler.gemini_pool["G01"]
    assert lane.requests_used == 0
    assert lane.requests_remaining == 3

    test_scheduler.select_lane_sync()
    assert lane.requests_used == 1
    assert lane.requests_remaining == 2


def test_13_credentials_never_appear_in_logs(caplog, test_scheduler):
    """13. Test logs contain lane_id and provider details without raw secret API key values."""
    mock_gemini = AsyncMock(spec=LLMProvider)
    mock_gemini.generate_async.return_value = "Mock Answer"

    gateway = LLMGateway(scheduler=test_scheduler, gemini_adapter=mock_gemini)

    with caplog.at_level(logging.INFO):
        asyncio.run(gateway.generate_async("Test query"))

    log_text = caplog.text
    assert "mock-gemini-key" not in log_text
    assert "mock-nemotron-key" not in log_text
    assert "[LLM_ROUTE] provider=gemini lane=G01" in log_text


@pytest.mark.anyio
async def test_14_streaming_keeps_lane_occupied_until_completion(test_scheduler):
    """14. Test streaming generator holds active_requests=1 for its entire lifetime."""
    lane = test_scheduler.gemini_pool["G01"]

    async def mock_stream_chunks():
        yield 'data: {"candidates": [{"content": {"parts": [{"text": "Hello"}]}}]}\n\n'
        assert lane.active_requests == 1

    mock_client = MagicMock()
    mock_cm = MagicMock()
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.aiter_lines = mock_stream_chunks
    mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
    mock_cm.__aexit__ = AsyncMock(return_value=None)
    mock_client.stream.return_value = mock_cm

    gateway = LLMGateway(scheduler=test_scheduler)

    with patch("app.knowledge.rag.providers.get_shared_async_client", return_value=mock_client), \
         patch("app.knowledge.rag.llm_gateway.get_shared_async_client", return_value=mock_client):
        chunks = []
        async for chunk in gateway.generate_stream_async("Stream query"):
            chunks.append(chunk)

    assert "".join(chunks) == "Hello"
    assert lane.active_requests == 0


@pytest.mark.anyio
async def test_15_concurrent_requests_never_exceed_per_lane_concurrency(test_scheduler):
    """15. Test per-lane concurrency (max_concurrency=1) is strictly enforced under load."""
    selected_lanes = []

    async def send_req():
        lane, _, _ = await test_scheduler.select_lane_async()
        selected_lanes.append(lane)

    await asyncio.gather(*[send_req() for _ in range(5)])

    for lane in selected_lanes:
        assert lane.active_requests <= 1
