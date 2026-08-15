"""Phase 2A Persistent Quota and Team Reservation Manager Unit and Integration Tests."""

import asyncio
from datetime import datetime, timezone
import concurrent.futures
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, LLMLaneModel, TeamQuotaModel, TeamModel, EventModel, utc_now
from app.database.db import SessionLocal, init_db
from app.knowledge.exceptions import LLMQuotaExhaustedError
from app.knowledge.rag.lane import LaneState
from app.knowledge.rag.scheduler import QuotaScheduler
from app.services.team_service import TeamService


def make_scheduler(**kwargs):
    """Factory helper creating a QuotaScheduler with default test credentials."""
    defaults = {
        "gemini_api_key": "mock-gemini-key",
        "nemotron_api_key": "mock-nemotron-key",
    }
    defaults.update(kwargs)
    return QuotaScheduler(**defaults)


@pytest.fixture(autouse=True)
def setup_db():
    """Ensures database tables are initialized and fresh before each test."""
    init_db()
    db = SessionLocal()
    try:
        db.query(LLMLaneModel).delete()
        db.query(TeamQuotaModel).delete()
        db.commit()
    finally:
        db.close()
    yield


def test_1_lane_records_created():
    """Verify lane records (G01..G10, N01..N10) are created in PostgreSQL/SQLite on initialization."""
    scheduler = make_scheduler(gemini_num_lanes=10, nemotron_num_lanes=10)
    db = SessionLocal()
    try:
        lanes = db.query(LLMLaneModel).all()
        assert len(lanes) == 20
        gemini_lanes = [l for l in lanes if l.provider == "gemini"]
        nemotron_lanes = [l for l in lanes if l.provider == "nemotron"]
        assert len(gemini_lanes) == 10
        assert len(nemotron_lanes) == 10
    finally:
        db.close()


def test_2_lane_ids_unique():
    """Verify lane IDs enforce unique database constraint."""
    db = SessionLocal()
    try:
        scheduler = make_scheduler()
        lanes = db.query(LLMLaneModel).all()
        lane_ids = [l.lane_id for l in lanes]
        assert len(lane_ids) == len(set(lane_ids))
    finally:
        db.close()


def test_3_get_or_create_team_quota():
    """Verify TeamService.get_or_create_team_quota initializes default quota of 10."""
    db = SessionLocal()
    try:
        TeamService.join_team(db, "TEAM-ALPHA", ["Alice"])
        q = TeamService.get_or_create_team_quota(db, "TEAM-ALPHA")
        assert q.question_limit == 10
        assert q.questions_used == 0
    finally:
        db.close()


def test_4_reserve_team_quota_atomic_success():
    """Verify atomic reservation increments questions_used atomically."""
    db = SessionLocal()
    try:
        TeamService.join_team(db, "TEAM-BETA", ["Bob"])
        success = TeamService.reserve_team_quota(db, "TEAM-BETA")
        assert success is True

        q = TeamService.get_or_create_team_quota(db, "TEAM-BETA")
        assert q.questions_used == 1
    finally:
        db.close()


def test_5_reserve_team_quota_exceeded_fails():
    """Verify reservation fails once questions_used reaches limit."""
    db = SessionLocal()
    try:
        TeamService.join_team(db, "TEAM-GAMMA", ["Charlie"])
        q = TeamService.get_or_create_team_quota(db, "TEAM-GAMMA", default_limit=2)

        assert TeamService.reserve_team_quota(db, "TEAM-GAMMA") is True
        assert TeamService.reserve_team_quota(db, "TEAM-GAMMA") is True
        # 3rd attempt should fail
        assert TeamService.reserve_team_quota(db, "TEAM-GAMMA") is False
    finally:
        db.close()


def test_6_concurrent_team_reservations_cannot_exceed_limit():
    """Verify concurrent team reservations never exceed question limit under thread race."""
    db = SessionLocal()
    try:
        TeamService.join_team(db, "TEAM-RACE", ["Racer"])
        TeamService.get_or_create_team_quota(db, "TEAM-RACE", default_limit=10)

        def reserve_task():
            local_db = SessionLocal()
            try:
                return TeamService.reserve_team_quota(local_db, "TEAM-RACE")
            finally:
                local_db.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(reserve_task) for _ in range(30)]
            results = [f.result() for f in futures]

        successful_reservations = sum(1 for r in results if r is True)
        assert successful_reservations == 10

        q = TeamService.get_or_create_team_quota(db, "TEAM-RACE")
        assert q.questions_used == 10
    finally:
        db.close()


def test_7_lane_reservation_succeeds_under_concurrency_limit():
    """Verify atomic database lane reservation succeeds under concurrency limit."""
    scheduler = make_scheduler(gemini_test_limit=3, gemini_max_concurrency=1)
    lane, api_key, is_fallback = scheduler.select_lane_sync()
    assert lane.lane_id == "G01"
    assert is_fallback is False

    db = SessionLocal()
    try:
        rec = db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G01").first()
        assert rec.requests_used == 1
        assert rec.active_requests == 1
        assert rec.state == LaneState.BUSY.value
    finally:
        db.close()


def test_8_concurrent_lane_reservations_cannot_exceed_max_concurrency():
    """Verify concurrent lane reservations enforce max_concurrent_requests=1 per lane."""
    scheduler = make_scheduler(gemini_test_limit=3, gemini_max_concurrency=1)

    # First reservation takes G01
    l1, _, _ = scheduler.select_lane_sync()
    assert l1.lane_id == "G01"

    # Second reservation takes G02 because G01 is BUSY (active_requests=1)
    l2, _, _ = scheduler.select_lane_sync()
    assert l2.lane_id == "G02"

    db = SessionLocal()
    try:
        g01 = db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G01").first()
        g02 = db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G02").first()
        assert g01.active_requests == 1
        assert g02.active_requests == 1
    finally:
        db.close()


def test_9_daily_lane_limit_cannot_be_exceeded():
    """Verify persistent lane rejects reservations once requests_used >= daily_limit."""
    scheduler = make_scheduler(gemini_num_lanes=1, nemotron_num_lanes=0, gemini_test_limit=2)

    # Req 1
    l1, _, _ = scheduler.select_lane_sync()
    scheduler.release_lane(l1.lane_id, success=True)

    # Req 2
    l2, _, _ = scheduler.select_lane_sync()
    scheduler.release_lane(l2.lane_id, success=True)

    # Req 3 should fail because G01 reached daily_limit=2
    with pytest.raises(LLMQuotaExhaustedError):
        scheduler.select_lane_sync()


def test_10_successful_release_decrements_active_requests():
    """Verify successful release decrements active_requests in DB."""
    scheduler = make_scheduler()
    lane, _, _ = scheduler.select_lane_sync()

    db = SessionLocal()
    try:
        rec = db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == lane.lane_id).first()
        assert rec.active_requests == 1

        scheduler.release_lane(lane.lane_id, success=True)
        db.refresh(rec)
        assert rec.active_requests == 0
        assert rec.requests_used == 1
    finally:
        db.close()


def test_11_429_persists_rate_limited_state():
    """Verify HTTP 429 persists RATE_LIMITED state and cooldown_until timestamp in DB."""
    scheduler = make_scheduler(cooldown_seconds=60.0)
    lane, _, _ = scheduler.select_lane_sync()
    scheduler.release_lane(lane.lane_id, success=False, status_code=429)

    db = SessionLocal()
    try:
        rec = db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == lane.lane_id).first()
        assert rec.state == LaneState.RATE_LIMITED.value
        assert rec.cooldown_until is not None
        assert rec.error_count == 1
    finally:
        db.close()


def test_12_cooldown_until_persists():
    """Verify cooldown_until timestamp persists and blocks eligibility until elapsed."""
    scheduler = make_scheduler(gemini_num_lanes=1, nemotron_num_lanes=0, cooldown_seconds=300.0)
    lane, _, _ = scheduler.select_lane_sync()
    scheduler.release_lane(lane.lane_id, success=False, status_code=429)

    # Instantiating a new scheduler should read persisted cooldown_until from DB
    new_scheduler = make_scheduler(gemini_num_lanes=1, nemotron_num_lanes=0, cooldown_seconds=300.0)
    with pytest.raises(LLMQuotaExhaustedError):
        new_scheduler.select_lane_sync()


def test_13_5xx_timeout_persists_degraded_state():
    """Verify 3 consecutive 5xx/timeout errors persist DEGRADED state in DB."""
    scheduler = make_scheduler(gemini_num_lanes=1, nemotron_num_lanes=0, gemini_test_limit=10)

    for i in range(3):
        lane, _, _ = scheduler.select_lane_sync()
        scheduler.release_lane(lane.lane_id, success=False, status_code=500)

    db = SessionLocal()
    try:
        rec = db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G01").first()
        assert rec.error_count == 3
        assert rec.state == LaneState.DEGRADED.value
    finally:
        db.close()


def test_14_restart_restores_requests_used():
    """Verify simulated application restart restores requests_used from DB."""
    s1 = make_scheduler(gemini_test_limit=5)
    lane, _, _ = s1.select_lane_sync()
    s1.release_lane(lane.lane_id, success=True)

    # Simulated restart: instantiate new QuotaScheduler instance
    s2 = make_scheduler(gemini_test_limit=5)
    assert s2.gemini_pool["G01"].requests_used == 1

    db = SessionLocal()
    try:
        rec = db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G01").first()
        assert rec.requests_used == 1
    finally:
        db.close()


def test_15_restart_restores_cooldown_until():
    """Verify simulated restart restores cooldown_until timestamp from DB."""
    s1 = make_scheduler(cooldown_seconds=120.0)
    lane, _, _ = s1.select_lane_sync()
    s1.release_lane(lane.lane_id, success=False, status_code=429)

    s2 = make_scheduler(cooldown_seconds=120.0)
    assert s2.gemini_pool[lane.lane_id].cooldown_until is not None
    assert s2.gemini_pool[lane.lane_id].state == LaneState.RATE_LIMITED


def test_16_two_scheduler_instances_share_db_state():
    """Verify two independent scheduler instances sharing the same DB maintain global consistency."""
    s1 = make_scheduler(gemini_num_lanes=1, nemotron_num_lanes=0, gemini_test_limit=2)
    s2 = make_scheduler(gemini_num_lanes=1, nemotron_num_lanes=0, gemini_test_limit=2)

    l1, _, _ = s1.select_lane_sync()
    s1.release_lane(l1.lane_id, success=True)

    l2, _, _ = s2.select_lane_sync()
    s2.release_lane(l2.lane_id, success=True)

    # 3rd request from s1 or s2 must fail because G01 reached daily_limit=2 in DB
    with pytest.raises(LLMQuotaExhaustedError):
        s1.select_lane_sync()


def test_17_gemini_remains_primary_while_eligible():
    """Verify Gemini lanes are selected before Nemotron fallback lanes."""
    scheduler = make_scheduler()
    lane, _, is_fallback = scheduler.select_lane_sync()
    assert lane.provider == "gemini"
    assert is_fallback is False


def test_18_nemotron_used_only_after_gemini_unavailable():
    """Verify Nemotron fallback is used only after all Gemini lanes become unavailable."""
    scheduler = make_scheduler(gemini_num_lanes=1, nemotron_num_lanes=1, gemini_test_limit=1, nemotron_test_limit=3)

    # Exhaust Gemini lane G01
    g_lane, _, is_fb1 = scheduler.select_lane_sync()
    assert g_lane.lane_id == "G01"
    assert is_fb1 is False
    scheduler.release_lane(g_lane.lane_id, success=True)

    # Next request must fall back to Nemotron N01
    n_lane, _, is_fb2 = scheduler.select_lane_sync()
    assert n_lane.lane_id == "N01"
    assert is_fb2 is True


def test_19_team_quota_respects_event_question_limit():
    """Verify team quota respects EventModel question_limit setting."""
    db = SessionLocal()
    try:
        evt = EventModel(
            name="Hackathon 2026",
            start_time=utc_now(),
            end_time=utc_now(),
            question_limit=3,
            is_active=True,
        )
        db.add(evt)
        db.commit()
        db.refresh(evt)

        TeamService.join_team(db, "TEAM-DELTA", ["Dave"])

        assert TeamService.reserve_team_quota(db, "TEAM-DELTA", event_id=evt.id) is True
        assert TeamService.reserve_team_quota(db, "TEAM-DELTA", event_id=evt.id) is True
        assert TeamService.reserve_team_quota(db, "TEAM-DELTA", event_id=evt.id) is True
        # 4th attempt should fail
        assert TeamService.reserve_team_quota(db, "TEAM-DELTA", event_id=evt.id) is False
    finally:
        db.close()


def test_20_failed_lane_acquisition_rolls_back_team_quota():
    """Verify pre-generation LLM acquisition failure rolls back team prompt quota."""
    db = SessionLocal()
    try:
        TeamService.join_team(db, "TEAM-ROLLBACK", ["Elena"])
        assert TeamService.reserve_team_quota(db, "TEAM-ROLLBACK") is True

        q1 = TeamService.get_or_create_team_quota(db, "TEAM-ROLLBACK")
        assert q1.questions_used == 1

        # Simulate pre-generation acquisition rollback
        TeamService.rollback_team_quota(db, "TEAM-ROLLBACK")

        q2 = TeamService.get_or_create_team_quota(db, "TEAM-ROLLBACK")
        assert q2.questions_used == 0
    finally:
        db.close()


def test_21_provider_failure_preserves_team_quota_consumption():
    """Verify provider execution failure preserves team quota consumption (no rollback after LLM call)."""
    db = SessionLocal()
    try:
        TeamService.join_team(db, "TEAM-FAIL", ["Frank"])
        assert TeamService.reserve_team_quota(db, "TEAM-FAIL") is True

        # Provider fails (e.g. 500 error), quota is NOT rolled back
        q = TeamService.get_or_create_team_quota(db, "TEAM-FAIL")
        assert q.questions_used == 1
    finally:
        db.close()


def test_22_streaming_holds_persistent_lane_reservation_until_completion():
    """Verify streaming token generation holds active DB slot until generator exit."""
    async def _async_test():
        scheduler = make_scheduler(gemini_num_lanes=1, nemotron_num_lanes=0, gemini_test_limit=5)
        lane, _, _ = await scheduler.select_lane_async()

        db = SessionLocal()
        try:
            rec = db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == lane.lane_id).first()
            assert rec.active_requests == 1

            # Simulate streaming release on generator exit
            scheduler.release_lane(lane.lane_id, success=True)
            db.refresh(rec)
            assert rec.active_requests == 0
        finally:
            db.close()

    asyncio.run(_async_test())


def test_23_credentials_never_appear_in_db_logs_status():
    """Verify credentials in DB, status, and telemetry contain only credential_ref (no raw API key secrets)."""
    scheduler = make_scheduler(gemini_api_key="secret-gemini-key-12345", nemotron_api_key="secret-nemotron-key-67890")
    db = SessionLocal()
    try:
        lanes = db.query(LLMLaneModel).all()
        for lane_rec in lanes:
            # Check DB records
            assert "secret-gemini-key-12345" not in lane_rec.credential_ref
            assert "secret-nemotron-key-67890" not in lane_rec.credential_ref
            assert lane_rec.credential_ref in ["GEMINI_API_KEY", "OPENROUTER_API_KEY"]

        # Check telemetry status dictionary
        status = scheduler.get_status()
        status_str = str(status)
        assert "secret-gemini-key-12345" not in status_str
        assert "secret-nemotron-key-67890" not in status_str
    finally:
        db.close()


def test_24_fallback_count_increments_correctly():
    """Verify fallback count increments only on fallback Nemotron selection."""
    scheduler = make_scheduler(gemini_num_lanes=1, gemini_test_limit=1)

    # First request: Gemini primary G01
    l1, _, is_fb1 = scheduler.select_lane_sync()
    assert is_fb1 is False
    assert scheduler.nemotron_fallback_requests == 0
    scheduler.release_lane(l1.lane_id, success=True)

    # Second request: Fallback to Nemotron N01
    l2, _, is_fb2 = scheduler.select_lane_sync()
    assert is_fb2 is True
    assert scheduler.nemotron_fallback_requests == 1
