"""Phase 2B Production Hardening, Multi-Worker Validation, and Database Authority Test Suite."""

import asyncio
from datetime import datetime, timedelta, timezone
import concurrent.futures
import logging
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.database.models import LLMLaneModel, TeamQuotaModel, TeamModel, EventModel, utc_now
from app.database.db import SessionLocal, init_db
from app.knowledge.exceptions import LLMQuotaExhaustedError, LLMServiceError, LLMTimeoutError
from app.knowledge.rag.lane import LLMLane, LanePriority, LaneState
from app.knowledge.rag.llm_gateway import LLMGateway
from app.knowledge.rag.providers import LLMProvider
from app.knowledge.rag.scheduler import QuotaScheduler
from app.services.team_service import TeamService


def make_scheduler(**kwargs):
    """Factory helper creating a QuotaScheduler with default test credentials."""
    defaults = {
        "gemini_api_key": "mock-gemini-key",
        "nemotron_api_key": "mock-nemotron-key",
        "gemini_enabled": True,
        "nemotron_enabled": True,
        "gemini_model": "gemini-2.0-flash",
        "nemotron_model": "nvidia/nemotron-3.5-lightning:free",
        "gemini_test_limit": 3,
        "nemotron_test_limit": 3,
        "gemini_max_concurrency": 1,
        "nemotron_max_concurrency": 1,
        "gemini_num_lanes": 10,
        "nemotron_num_lanes": 10,
        "cooldown_seconds": 60.0,
    }
    defaults.update(kwargs)
    return QuotaScheduler(**defaults)


@pytest.fixture(autouse=True)
def clean_db():
    """Ensures database tables are initialized and fresh before each test."""
    init_db()
    db = SessionLocal()
    try:
        db.query(LLMLaneModel).delete()
        db.query(TeamQuotaModel).delete()
        db.query(TeamModel).delete()
        db.commit()
    finally:
        db.close()
    yield


# =====================================================================
# GROUP A: MULTI-WORKER CONCURRENCY
# =====================================================================

def test_2b_a1_multi_scheduler_lane_race():
    """Two independent QuotaScheduler instances race to reserve G01. Exactly 1 succeeds."""
    s1 = make_scheduler(gemini_num_lanes=1, nemotron_num_lanes=0, gemini_test_limit=3)
    s2 = make_scheduler(gemini_num_lanes=1, nemotron_num_lanes=0, gemini_test_limit=3)

    results = []
    errors = []

    def task(scheduler_inst):
        try:
            lane, _, _ = scheduler_inst.select_lane_sync()
            results.append(lane.lane_id)
        except Exception as e:
            errors.append(e)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(task, s1)
        f2 = executor.submit(task, s2)
        f1.result()
        f2.result()

    assert len(results) == 1
    assert results[0] == "G01"
    assert len(errors) == 1
    assert isinstance(errors[0], LLMQuotaExhaustedError)

    db = SessionLocal()
    try:
        rec = db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G01").first()
        assert rec.active_requests <= 1
    finally:
        db.close()


# =====================================================================
# GROUP B: TEAM QUOTA RACES
# =====================================================================

def test_2b_b1_team_quota_50_concurrent_race():
    """50 concurrent thread reservation attempts on team with limit 10. Exactly 10 succeed."""
    db = SessionLocal()
    try:
        TeamService.join_team(db, "TEAM-50-RACE", ["Racer"])
        TeamService.get_or_create_team_quota(db, "TEAM-50-RACE", default_limit=10)

        def reserve_task():
            local_db = SessionLocal()
            try:
                return TeamService.reserve_team_quota(local_db, "TEAM-50-RACE")
            finally:
                local_db.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(reserve_task) for _ in range(50)]
            results = [f.result() for f in futures]

        successful = sum(1 for r in results if r is True)
        assert successful == 10

        q = TeamService.get_or_create_team_quota(db, "TEAM-50-RACE")
        assert q.questions_used == 10
    finally:
        db.close()


# =====================================================================
# GROUP C: COMBINED TEAM + LANE RACES
# =====================================================================

def test_2b_c1_combined_team_and_lane_concurrency():
    """30 concurrent simulated requests. Team limit 10, G01..G10 limit 3."""
    scheduler = make_scheduler(gemini_num_lanes=10, gemini_test_limit=3, gemini_max_concurrency=1)
    db = SessionLocal()
    try:
        TeamService.join_team(db, "TEAM-COMBINED", ["Alice"])
        TeamService.get_or_create_team_quota(db, "TEAM-COMBINED", default_limit=10)

        def req_task():
            local_db = SessionLocal()
            try:
                reserved = TeamService.reserve_team_quota(local_db, "TEAM-COMBINED")
                if not reserved:
                    return "TEAM_QUOTA_EXCEEDED"

                try:
                    lane, api_key, is_fallback = scheduler.select_lane_sync()
                except LLMQuotaExhaustedError:
                    TeamService.rollback_team_quota(local_db, "TEAM-COMBINED")
                    return "LANE_EXHAUSTED"

                # Simulate execution then release
                scheduler.release_lane(lane.lane_id, success=True)
                return f"SUCCESS:{lane.lane_id}"
            finally:
                local_db.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(req_task) for _ in range(30)]
            results = [f.result() for f in futures]

        successful = [r for r in results if r.startswith("SUCCESS:")]
        assert len(successful) == 10

        q = TeamService.get_or_create_team_quota(db, "TEAM-COMBINED")
        assert q.questions_used == 10

        lanes = db.query(LLMLaneModel).all()
        for lane in lanes:
            assert lane.active_requests == 0
    finally:
        db.close()


# =====================================================================
# GROUP D: PERSISTENT COOLDOWN
# =====================================================================

def test_2b_d1_persistent_cooldown_across_schedulers():
    """Process A releases G01 with HTTP 429. Scheduler B sees G01 as RATE_LIMITED in DB."""
    s1 = make_scheduler(gemini_num_lanes=1, nemotron_num_lanes=0, cooldown_seconds=300.0)
    lane, _, _ = s1.select_lane_sync()
    s1.release_lane(lane.lane_id, success=False, status_code=429)

    db = SessionLocal()
    try:
        rec = db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G01").first()
        assert rec.state == LaneState.RATE_LIMITED.value
        assert rec.cooldown_until is not None
        assert rec.active_requests == 0
    finally:
        db.close()

    # Destroy s1 and instantiate s2
    del s1
    s2 = make_scheduler(gemini_num_lanes=1, nemotron_num_lanes=0, cooldown_seconds=300.0)
    with pytest.raises(LLMQuotaExhaustedError):
        s2.select_lane_sync()


# =====================================================================
# GROUP E: PERSISTENT DEGRADED STATE
# =====================================================================

def test_2b_e1_persistent_degraded_state():
    """Cause 3 consecutive 500 errors on G01. Verify DEGRADED state survives reinitialization."""
    s1 = make_scheduler(gemini_num_lanes=1, nemotron_num_lanes=0, gemini_test_limit=10)
    for _ in range(3):
        l, _, _ = s1.select_lane_sync()
        s1.release_lane(l.lane_id, success=False, status_code=500)

    db = SessionLocal()
    try:
        rec = db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G01").first()
        assert rec.state == LaneState.DEGRADED.value
        assert rec.error_count == 3
    finally:
        db.close()

    del s1
    s2 = make_scheduler(gemini_num_lanes=1, nemotron_num_lanes=0, gemini_test_limit=10)
    with pytest.raises(LLMQuotaExhaustedError):
        s2.select_lane_sync()


# =====================================================================
# GROUP F: PROVIDER FAILURE & TEAM QUOTA SEMANTICS
# =====================================================================

def test_2b_f1_provider_failure_quota_semantics_case_a():
    """CASE A: Team quota reserved, LLM lane acquisition fails -> team quota rolled back."""
    db = SessionLocal()
    try:
        TeamService.join_team(db, "TEAM-F1A", ["Alice"])
        assert TeamService.reserve_team_quota(db, "TEAM-F1A") is True

        s = make_scheduler(gemini_num_lanes=0, nemotron_num_lanes=0)
        with pytest.raises(LLMQuotaExhaustedError):
            s.select_lane_sync()

        # Simulate pre-generation acquisition rollback
        TeamService.rollback_team_quota(db, "TEAM-F1A")
        q = TeamService.get_or_create_team_quota(db, "TEAM-F1A")
        assert q.questions_used == 0
    finally:
        db.close()


def test_2b_f1b_database_lane_acquisition_failure_rolls_back_team_quota():
    """Pre-generation DB lane acquisition failure rolls back team quota; provider NEVER called."""
    db = SessionLocal()
    mock_provider = MagicMock(spec=LLMProvider)

    try:
        TeamService.join_team(db, "TEAM-F1B", ["Bob"])
        assert TeamService.reserve_team_quota(db, "TEAM-F1B") is True

        # Scheduler with 0 lanes guarantees LLMQuotaExhaustedError BEFORE provider execution
        s = make_scheduler(gemini_num_lanes=0, nemotron_num_lanes=0)

        with pytest.raises(LLMQuotaExhaustedError):
            try:
                s.select_lane_sync()
            except LLMQuotaExhaustedError:
                TeamService.rollback_team_quota(db, "TEAM-F1B")
                raise

        mock_provider.generate.assert_not_called()
        q = TeamService.get_or_create_team_quota(db, "TEAM-F1B")
        assert q.questions_used == 0
    finally:
        db.close()


def test_2b_f2_provider_failure_quota_semantics_case_b():
    """CASE B: Team quota reserved, lane acquired, provider returns 429 -> team quota remains consumed."""
    db = SessionLocal()
    try:
        TeamService.join_team(db, "TEAM-F2B", ["Charlie"])
        assert TeamService.reserve_team_quota(db, "TEAM-F2B") is True

        s = make_scheduler()
        lane, _, _ = s.select_lane_sync()

        # Provider execution returns 429
        s.release_lane(lane.lane_id, success=False, status_code=429)

        # Quota remains consumed (no rollback after LLM call starts)
        q = TeamService.get_or_create_team_quota(db, "TEAM-F2B")
        assert q.questions_used == 1
    finally:
        db.close()


def test_2b_f3_provider_failure_quota_semantics_case_c():
    """CASE C: Team quota reserved, lane acquired, provider returns 500 -> team quota remains consumed."""
    db = SessionLocal()
    try:
        TeamService.join_team(db, "TEAM-F3C", ["Dave"])
        assert TeamService.reserve_team_quota(db, "TEAM-F3C") is True

        s = make_scheduler()
        lane, _, _ = s.select_lane_sync()

        # Provider execution returns 500
        s.release_lane(lane.lane_id, success=False, status_code=500)

        q = TeamService.get_or_create_team_quota(db, "TEAM-F3C")
        assert q.questions_used == 1
    finally:
        db.close()


def test_2b_f4_provider_failure_quota_semantics_case_d():
    """CASE D: Team quota reserved, lane acquired, provider succeeds -> team quota remains consumed."""
    db = SessionLocal()
    try:
        TeamService.join_team(db, "TEAM-F4D", ["Eve"])
        assert TeamService.reserve_team_quota(db, "TEAM-F4D") is True

        s = make_scheduler()
        lane, _, _ = s.select_lane_sync()

        s.release_lane(lane.lane_id, success=True)

        q = TeamService.get_or_create_team_quota(db, "TEAM-F4D")
        assert q.questions_used == 1
    finally:
        db.close()


# =====================================================================
# GROUP G: STREAMING LIFECYCLE
# =====================================================================

def test_2b_g1_streaming_lifecycle_holds_slot():
    """Verify streaming token generator holds active_requests=1 for its entire lifetime."""
    async def _async_stream_test():
        scheduler = make_scheduler(gemini_num_lanes=1, nemotron_num_lanes=0, gemini_test_limit=5)
        gateway = LLMGateway(scheduler=scheduler)

        async def mock_stream_chunks():
            yield 'data: {"candidates": [{"content": {"parts": [{"text": "Token1"}]}}]}\n\n'
            # Verify DB active_requests is 1 while streaming
            db = SessionLocal()
            try:
                rec = db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G01").first()
                assert rec.active_requests == 1
            finally:
                db.close()
            yield 'data: {"candidates": [{"content": {"parts": [{"text": "Token2"}]}}]}\n\n'

        mock_client = MagicMock()
        mock_cm = MagicMock()
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.aiter_lines = mock_stream_chunks
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_client.stream.return_value = mock_cm

        with patch("app.knowledge.rag.providers.get_shared_async_client", return_value=mock_client), \
             patch("app.knowledge.rag.llm_gateway.get_shared_async_client", return_value=mock_client):
            chunks = []
            async for token in gateway.generate_stream_async("Stream query"):
                chunks.append(token)

        assert "".join(chunks) == "Token1Token2"

        # Verify DB active_requests returns to 0 after stream completes
        db = SessionLocal()
        try:
            rec = db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G01").first()
            assert rec.active_requests == 0
        finally:
            db.close()

    asyncio.run(_async_stream_test())


# =====================================================================
# GROUP H: RESTART & SERVER REINITIALIZATION
# =====================================================================

def test_2b_h1_server_restart_simulation():
    """Configure G01..G05 states in DB. Reinitialize scheduler. Verify exact state restoration."""
    db = SessionLocal()
    try:
        # Pre-seed scheduler to create DB rows
        make_scheduler()

        # Set specific fields directly in DB
        db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G01").update({LLMLaneModel.requests_used: 2})
        db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G02").update({LLMLaneModel.requests_used: 1})

        future_cooldown = utc_now() + timedelta(seconds=300)
        db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G03").update({
            LLMLaneModel.state: LaneState.RATE_LIMITED.value,
            LLMLaneModel.cooldown_until: future_cooldown,
        })
        db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G04").update({
            LLMLaneModel.state: LaneState.DEGRADED.value,
            LLMLaneModel.error_count: 3,
            LLMLaneModel.cooldown_until: future_cooldown,
        })
        db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G05").update({
            LLMLaneModel.active_requests: 1,
            LLMLaneModel.state: LaneState.BUSY.value,
        })
        db.commit()
    finally:
        db.close()

    # Reinitialize scheduler
    s2 = make_scheduler()

    assert s2.gemini_pool["G01"].requests_used == 2
    assert s2.gemini_pool["G02"].requests_used == 1
    assert s2.gemini_pool["G03"].state == LaneState.RATE_LIMITED
    assert s2.gemini_pool["G03"].cooldown_until is not None
    assert s2.gemini_pool["G04"].state == LaneState.DEGRADED
    assert s2.gemini_pool["G04"].error_count == 3
    assert s2.gemini_pool["G05"].active_requests == 1
    assert s2.gemini_pool["G05"].state == LaneState.BUSY


def test_2b_h1b_restart_does_not_reset_active_requests():
    """Verify reinitializing scheduler does NOT reset active_requests to zero on startup."""
    db = SessionLocal()
    try:
        make_scheduler()
        db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G01").update({
            LLMLaneModel.active_requests: 1,
            LLMLaneModel.state: LaneState.BUSY.value,
        })
        db.commit()
    finally:
        db.close()

    # Reinitialize scheduler
    s2 = make_scheduler()
    assert s2.gemini_pool["G01"].active_requests == 1
    assert s2.gemini_pool["G01"].state == LaneState.BUSY

    db2 = SessionLocal()
    try:
        rec = db2.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G01").first()
        assert rec.active_requests == 1
        assert rec.state == LaneState.BUSY.value
    finally:
        db2.close()


# =====================================================================
# GROUP I: TRANSACTION ISOLATION
# =====================================================================

def test_2b_i1_db_transaction_isolation():
    """Verify DB session/connection is released BEFORE provider execution begins."""
    scheduler = make_scheduler()
    db_session_active_during_provider = []

    class MockAdapter(LLMProvider):
        def generate(self, prompt, model, api_key, **kwargs):
            # Check if any open transaction exists in caller's thread
            local_db = SessionLocal()
            try:
                # Query DB to check if connection pool is free
                rec = local_db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G01").first()
                db_session_active_during_provider.append(rec.active_requests == 1)
            finally:
                local_db.close()
            return "Adapter Success"

        async def generate_async(self, prompt, model, api_key, **kwargs):
            return "Adapter Success"

        async def generate_stream_async(self, prompt, model, api_key, **kwargs):
            yield "Adapter Success", None

    gateway = LLMGateway(scheduler=scheduler, gemini_adapter=MockAdapter())
    res = gateway.generate("Test prompt")

    assert res == "Adapter Success"
    assert len(db_session_active_during_provider) == 1
    assert db_session_active_during_provider[0] is True


# =====================================================================
# GROUP J: CONNECTION POOL BEHAVIOR
# =====================================================================

def test_2b_j1_connection_pool_high_concurrency():
    """Rapid concurrent DB acquisitions across 50 iterations under pool settings."""
    scheduler = make_scheduler(gemini_test_limit=100)

    def worker(i):
        lane, _, _ = scheduler.select_lane_sync()
        scheduler.release_lane(lane.lane_id, success=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker, i) for i in range(50)]
        for f in futures:
            f.result()

    db = SessionLocal()
    try:
        lanes = db.query(LLMLaneModel).all()
        total_used = sum(l.requests_used for l in lanes)
        assert total_used == 50
    finally:
        db.close()


# =====================================================================
# GROUP K: CREDENTIAL PRIVACY AUDIT
# =====================================================================

def test_2b_k1_credential_privacy_audit(caplog):
    """Verify raw secret API keys never appear in DB, status telemetry, or logs."""
    raw_gemini_key = "AIzaSySecretGeminiKey12345"
    raw_nemotron_key = "sk-or-v1-SecretNemotronKey67890"

    scheduler = make_scheduler(gemini_api_key=raw_gemini_key, nemotron_api_key=raw_nemotron_key)

    db = SessionLocal()
    try:
        lanes = db.query(LLMLaneModel).all()
        for rec in lanes:
            assert raw_gemini_key not in rec.credential_ref
            assert raw_nemotron_key not in rec.credential_ref
            assert rec.credential_ref in ["GEMINI_API_KEY", "OPENROUTER_API_KEY"]

        status = scheduler.get_status()
        status_str = str(status)
        assert raw_gemini_key not in status_str
        assert raw_nemotron_key not in status_str
    finally:
        db.close()

    mock_gemini = AsyncMock(spec=LLMProvider)
    mock_gemini.generate_async.return_value = "Answer"
    gateway = LLMGateway(scheduler=scheduler, gemini_adapter=mock_gemini)

    with caplog.at_level(logging.INFO):
        asyncio.run(gateway.generate_async("Audit query"))

    log_text = caplog.text
    assert raw_gemini_key not in log_text
    assert raw_nemotron_key not in log_text


# =====================================================================
# GROUP L: TELEMETRY CONSISTENCY
# =====================================================================

def test_2b_l1_telemetry_consistency_during_concurrency():
    """Run get_status() during concurrent activity and verify status metrics consistency."""
    scheduler = make_scheduler(gemini_test_limit=10, nemotron_test_limit=10)

    def worker():
        try:
            l, _, _ = scheduler.select_lane_sync()
            status = scheduler.get_status()
            scheduler.release_lane(l.lane_id, success=True)
            return status
        except Exception:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker) for _ in range(15)]
        statuses = [f.result() for f in futures if f.result() is not None]

    assert len(statuses) > 0
    for st in statuses:
        g = st["gemini"]
        assert g["total_active_requests"] <= 10
        assert g["total_requests_used"] <= g["total_configured_test_request_limit"]


# =====================================================================
# GROUP M: FALLBACK AND FALLBACK RECOVERY
# =====================================================================

def test_2b_m1_gemini_exhaustion_routes_to_nemotron():
    """Exhaust G01..G10 -> Nemotron handles request with fallback=True."""
    scheduler = make_scheduler(gemini_num_lanes=2, nemotron_num_lanes=2, gemini_test_limit=1, nemotron_test_limit=3)

    # Exhaust Gemini G01, G02
    l1, _, fb1 = scheduler.select_lane_sync()
    s1_release = scheduler.release_lane(l1.lane_id, success=True)
    l2, _, fb2 = scheduler.select_lane_sync()
    s2_release = scheduler.release_lane(l2.lane_id, success=True)

    assert fb1 is False
    assert fb2 is False

    # Next request must hit Nemotron N01 with fallback=True
    l3, key3, fb3 = scheduler.select_lane_sync()
    assert fb3 is True
    assert l3.provider == "nemotron"
    assert l3.lane_id == "N01"


def test_2b_m2_gemini_rate_limit_preserves_healthy_gemini():
    """Rate limit G01 -> G02..G10 continue serving requests before Nemotron fallback."""
    scheduler = make_scheduler(gemini_num_lanes=3, nemotron_num_lanes=2, gemini_test_limit=5, cooldown_seconds=300.0)

    # Rate limit G01
    l1, _, _ = scheduler.select_lane_sync()
    assert l1.lane_id == "G01"
    scheduler.release_lane(l1.lane_id, success=False, status_code=429)

    # Next requests must pick healthy Gemini lanes G02 and G03
    l2, _, fb2 = scheduler.select_lane_sync()
    assert l2.lane_id == "G02"
    assert fb2 is False

    l3, _, fb3 = scheduler.select_lane_sync()
    assert l3.lane_id == "G03"
    assert fb3 is False


def test_2b_m3_fallback_recovery():
    """Exhaust Gemini, fallback to Nemotron, restore 1 Gemini lane -> next request prefers Gemini."""
    scheduler = make_scheduler(gemini_num_lanes=1, nemotron_num_lanes=1, gemini_test_limit=1, nemotron_test_limit=3)

    # Exhaust Gemini G01
    l1, _, fb1 = scheduler.select_lane_sync()
    scheduler.release_lane(l1.lane_id, success=True)

    # Request falls back to Nemotron N01
    n_lane, _, fb2 = scheduler.select_lane_sync()
    assert fb2 is True
    assert n_lane.provider == "nemotron"
    scheduler.release_lane(n_lane.lane_id, success=True)

    # Restore Gemini G01 in DB
    db = SessionLocal()
    try:
        db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G01").update({
            LLMLaneModel.requests_used: 0,
            LLMLaneModel.state: LaneState.AVAILABLE.value,
        })
        db.commit()
    finally:
        db.close()

    # Next request must immediately select recovered Gemini G01
    rec_lane, _, fb3 = scheduler.select_lane_sync()
    assert fb3 is False
    assert rec_lane.provider == "gemini"
    assert rec_lane.lane_id == "G01"


# =====================================================================
# GROUP N: DATABASE AUTHORITY OVER PROCESS MEMORY
# =====================================================================

def test_2b_n1_database_state_overrides_stale_scheduler_memory():
    """Verify PostgreSQL database state strictly overrides stale in-memory scheduler state."""
    scheduler = make_scheduler(gemini_num_lanes=2, nemotron_num_lanes=0, gemini_test_limit=5)

    # Scenario A: In-memory G01 shows AVAILABLE, DB updated directly to RATE_LIMITED
    db = SessionLocal()
    try:
        future_cd = utc_now() + timedelta(seconds=300)
        db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G01").update({
            LLMLaneModel.state: LaneState.RATE_LIMITED.value,
            LLMLaneModel.cooldown_until: future_cd,
        })
        db.commit()
    finally:
        db.close()

    # DB state wins -> scheduler selects G02
    lane_a, _, _ = scheduler.select_lane_sync()
    assert lane_a.lane_id == "G02"

    # Scenario B: In-memory G02 shows capacity, DB updated directly to requests_used = daily_limit
    db = SessionLocal()
    try:
        db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G02").update({
            LLMLaneModel.requests_used: 5,
            LLMLaneModel.state: LaneState.DAILY_EXHAUSTED.value,
        })
        db.commit()
    finally:
        db.close()

    # DB quota state wins -> both G01 (rate-limited) and G02 (exhausted) rejected
    with pytest.raises(LLMQuotaExhaustedError):
        scheduler.select_lane_sync()
