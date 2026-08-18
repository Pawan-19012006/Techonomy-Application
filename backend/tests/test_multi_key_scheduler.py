"""Comprehensive tests for 20 API Key Load Balancing, Quota Scheduling, and Fallback mapping."""

import pytest
from app.config import Settings
from app.database.db import SessionLocal, init_db
from app.database.models import LLMLaneModel, TeamModel, TeamQuotaModel
from app.knowledge.exceptions import LLMQuotaExhaustedError
from app.knowledge.rag.lane import LaneState
from app.knowledge.rag.scheduler import QuotaScheduler
from app.services.team_service import TeamService


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
    except Exception:
        db.rollback()
    finally:
        db.close()
    yield


def test_20_keys_config_properties():
    """Verify gemini_api_keys_list and openrouter_api_keys_list load 10 keys cleanly."""
    settings = Settings(
        GEMINI_API_KEY_1="g_key_1",
        GEMINI_API_KEY_2="g_key_2",
        GEMINI_API_KEY_10="g_key_10",
        OPENROUTER_API_KEY_1="o_key_1",
        OPENROUTER_API_KEY_5="o_key_5",
        OPENROUTER_API_KEY_10="o_key_10",
    )

    g_keys = settings.gemini_api_keys_list
    assert len(g_keys) == 10
    assert g_keys[0] == "g_key_1"
    assert g_keys[1] == "g_key_2"
    assert g_keys[9] == "g_key_10"

    o_keys = settings.openrouter_api_keys_list
    assert len(o_keys) == 10
    assert o_keys[0] == "o_key_1"
    assert o_keys[4] == "o_key_5"
    assert o_keys[9] == "o_key_10"


def test_lane_credential_ref_mapping():
    """Verify G01..G10 map to GEMINI_API_KEY_1..10 and N01..N10 map to OPENROUTER_API_KEY_1..10."""
    g_keys = [f"gemini_secret_key_{i}" for i in range(1, 11)]
    o_keys = [f"openrouter_secret_key_{i}" for i in range(1, 11)]

    scheduler = QuotaScheduler(
        gemini_api_keys=g_keys,
        openrouter_api_keys=o_keys,
        gemini_enabled=True,
        nemotron_enabled=True,
    )

    for i in range(1, 11):
        lane_id_g = f"G{i:02d}"
        lane_g = scheduler.gemini_pool[lane_id_g]
        assert lane_g.credential_ref == f"GEMINI_API_KEY_{i}"
        assert scheduler.get_api_key_for_lane(lane_g) == f"gemini_secret_key_{i}"

        lane_id_n = f"N{i:02d}"
        lane_n = scheduler.nemotron_pool[lane_id_n]
        assert lane_n.credential_ref == f"OPENROUTER_API_KEY_{i}"
        assert scheduler.get_api_key_for_lane(lane_n) == f"openrouter_secret_key_{i}"


def test_gemini_primary_preference():
    """Verify Gemini primary pool is preferred over Nemotron when Gemini lanes are available."""
    g_keys = [f"gemini_secret_{i}" for i in range(1, 11)]
    o_keys = [f"openrouter_secret_{i}" for i in range(1, 11)]

    scheduler = QuotaScheduler(
        gemini_api_keys=g_keys,
        openrouter_api_keys=o_keys,
        gemini_enabled=True,
        nemotron_enabled=True,
    )

    lane, api_key, is_fallback = scheduler.select_lane_sync()
    assert is_fallback is False
    assert lane.provider == "gemini"
    assert lane.lane_id == "G01"
    assert api_key == "gemini_secret_1"
    scheduler.release_lane(lane.lane_id, success=True)


def test_nemotron_fallback_when_gemini_disabled_or_exhausted():
    """Verify scheduler falls back to N01..N10 when all Gemini lanes are disabled or exhausted."""
    g_keys = [f"g_key_{i}" for i in range(1, 11)]
    o_keys = [f"o_key_{i}" for i in range(1, 11)]

    scheduler = QuotaScheduler(
        gemini_api_keys=g_keys,
        openrouter_api_keys=o_keys,
        gemini_enabled=False,  # Disable Gemini
        nemotron_enabled=True,
    )

    lane, api_key, is_fallback = scheduler.select_lane_sync()
    assert is_fallback is True
    assert lane.provider == "nemotron"
    assert lane.lane_id == "N01"
    assert api_key == "o_key_1"
    scheduler.release_lane(lane.lane_id, success=True)


def test_team_quota_absolute_gate():
    """Verify team quota strictly rejects 11th question even if Nemotron capacity exists."""
    db = SessionLocal()
    try:
        test_team = "TEST_QUOTA_GATE_TEAM"
        TeamService.join_team(db, team_name=test_team, member_names=[test_team])
        quota_rec = TeamService.get_or_create_team_quota(db, team_name=test_team, default_limit=10)
        quota_rec.questions_used = 10
        db.commit()

        # Attempt to reserve 11th prompt slot
        reserved = TeamService.reserve_team_quota(db, team_name=test_team)
        assert reserved is False, "11th question must be rejected by team quota"
    finally:
        db.close()


def test_legacy_single_key_fallback():
    """Verify single GEMINI_API_KEY/OPENROUTER_API_KEY fallback works when specific _1..10 keys are not set."""
    scheduler = QuotaScheduler(
        gemini_api_key="fallback_gemini_single_key",
        nemotron_api_key="fallback_openrouter_single_key",
        gemini_api_keys=[""] * 10,
        openrouter_api_keys=[""] * 10,
        gemini_enabled=True,
        nemotron_enabled=True,
    )

    lane_g = scheduler.gemini_pool["G01"]
    assert scheduler.get_api_key_for_lane(lane_g) == "fallback_gemini_single_key"

    lane_n = scheduler.nemotron_pool["N01"]
    assert scheduler.get_api_key_for_lane(lane_n) == "fallback_openrouter_single_key"


def test_50_request_quota_per_lane():
    """Verify default request limit per lane is 50 for all 20 lanes (G01..G10 and N01..N10)."""
    scheduler = QuotaScheduler(
        gemini_api_key="g_key",
        nemotron_api_key="n_key",
        gemini_enabled=True,
        nemotron_enabled=True,
    )

    assert len(scheduler.gemini_pool) == 10
    assert len(scheduler.nemotron_pool) == 10

    for lane_id, lane in scheduler.gemini_pool.items():
        assert lane.configured_test_request_limit == 50, f"Gemini lane {lane_id} daily_limit must be 50"

    for lane_id, lane in scheduler.nemotron_pool.items():
        assert lane.configured_test_request_limit == 50, f"Nemotron lane {lane_id} daily_limit must be 50"


def test_single_lane_exhaustion_does_not_exhaust_sibling_lanes():
    """Verify G01 reaching 50 requests does NOT exhaust G02..G10 or N01..N10."""
    g_keys = [f"g_key_{i}" for i in range(1, 11)]
    o_keys = [f"o_key_{i}" for i in range(1, 11)]

    scheduler = QuotaScheduler(
        gemini_api_keys=g_keys,
        openrouter_api_keys=o_keys,
        gemini_enabled=True,
        nemotron_enabled=True,
    )

    # Manually exhaust G01 in DB so scheduler sync picks up persistent state
    db = SessionLocal()
    try:
        db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G01").update({
            LLMLaneModel.requests_used: 50,
            LLMLaneModel.state: LaneState.DAILY_EXHAUSTED.value,
        })
        db.commit()
    finally:
        db.close()

    # Next select_lane_sync must pick G02
    lane, api_key, is_fallback = scheduler.select_lane_sync()
    assert is_fallback is False
    assert lane.lane_id == "G02"
    assert api_key == "g_key_2"
    scheduler.release_lane(lane.lane_id, success=True)


def test_single_lane_rate_limit_isolation():
    """Verify one Gemini lane receiving HTTP 429 rate limit does NOT block sibling Gemini lanes."""
    g_keys = [f"g_key_{i}" for i in range(1, 11)]
    scheduler = QuotaScheduler(
        gemini_api_keys=g_keys,
        gemini_enabled=True,
        nemotron_enabled=False,
    )

    # Reserve G01 and simulate 429 rate limit response
    lane1, _, _ = scheduler.select_lane_sync()
    assert lane1.lane_id == "G01"
    scheduler.release_lane("G01", success=False, status_code=429, error=Exception("HTTP 429 Rate Limit"))

    assert scheduler.gemini_pool["G01"].state == LaneState.RATE_LIMITED

    # Next reservation must seamlessly pick G02
    lane2, api_key, is_fallback = scheduler.select_lane_sync()
    assert is_fallback is False
    assert lane2.lane_id == "G02"
    assert api_key == "g_key_2"
    scheduler.release_lane("G02", success=True)


def test_http_max_connections_distinct_from_api_quota():
    """Verify HTTP connection limits in providers.py are connection transport limits, not API quotas."""
    from app.knowledge.rag.providers import get_shared_async_client, get_shared_sync_client
    
    sync_client = get_shared_sync_client()
    assert sync_client._transport._pool._max_connections == 50

    # API quota setting is distinct (50 requests per lane)
    scheduler = QuotaScheduler(gemini_enabled=True)
    assert scheduler.gemini_pool["G01"].configured_test_request_limit == 50

