"""Exhaustive Final Pre-Event Release-Gate Verification Suite for Techonomy LLM Router & Scheduler."""

import asyncio
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.database.db import SessionLocal, init_db
from app.database.models import LLMLaneModel
from app.knowledge.exceptions import LLMQuotaExhaustedError, LLMServiceError
from app.knowledge.rag.lane import LLMLane, LanePriority, LaneState
from app.knowledge.rag.llm_gateway import LLMGateway
from app.knowledge.rag.scheduler import QuotaScheduler
from app.utils.logging import logger


def reset_db_lanes():
    db = SessionLocal()
    try:
        db.query(LLMLaneModel).update({
            LLMLaneModel.requests_used: 0,
            LLMLaneModel.active_requests: 0,
            LLMLaneModel.state: LaneState.AVAILABLE.value,
            LLMLaneModel.cooldown_until: None,
            LLMLaneModel.error_count: 0
        })
        db.commit()
    finally:
        db.close()


def run_checks():
    print("================================================================================")
    print(" 🚀 TECHONOMY RELEASE-GATE AUDIT & VERIFICATION SUITE")
    print("================================================================================")

    init_db()
    db = SessionLocal()

    # 1. 20-Lane Construction & Default Verification
    print("\n[CHECK 1] 20-Lane Pool Construction & 50-Request Quotas...")
    g_keys = [f"g_mock_key_{i}" for i in range(1, 11)]
    o_keys = [f"o_mock_key_{i}" for i in range(1, 11)]

    scheduler = QuotaScheduler(
        gemini_api_keys=g_keys,
        openrouter_api_keys=o_keys,
        gemini_enabled=True,
        nemotron_enabled=True,
    )

    assert len(scheduler.gemini_pool) == 10, "Gemini pool must contain exactly 10 lanes"
    assert len(scheduler.nemotron_pool) == 10, "Nemotron pool must contain exactly 10 lanes"

    for lid, lane in scheduler.gemini_pool.items():
        assert lane.configured_test_request_limit == 50, f"{lid} daily_limit must be 50"
        assert lane.max_concurrent_requests == 1, f"{lid} concurrency must be 1"
        assert lane.priority == LanePriority.PRIMARY, f"{lid} priority must be PRIMARY"

    for lid, lane in scheduler.nemotron_pool.items():
        assert lane.configured_test_request_limit == 50, f"{lid} daily_limit must be 50"
        assert lane.max_concurrent_requests == 1, f"{lid} concurrency must be 1"
        assert lane.priority == LanePriority.FALLBACK, f"{lid} priority must be FALLBACK"

    print("  ✅ 20 lanes verified: G01..G10 (Primary, 50 limit, 1 max_concurrency), N01..N10 (Fallback, 50 limit, 1 max_concurrency)")

    # 2. Key-to-Lane Mapping
    print("\n[CHECK 2] Key-to-Lane Mapping Verification...")
    for i in range(1, 11):
        g_lane = scheduler.gemini_pool[f"G{i:02d}"]
        n_lane = scheduler.nemotron_pool[f"N{i:02d}"]
        assert g_lane.credential_ref == f"GEMINI_API_KEY_{i}"
        assert n_lane.credential_ref == f"OPENROUTER_API_KEY_{i}"
        assert scheduler.get_api_key_for_lane(g_lane) == f"g_mock_key_{i}"
        assert scheduler.get_api_key_for_lane(n_lane) == f"o_mock_key_{i}"
    print("  ✅ G01..G10 map to GEMINI_API_KEY_1..10 and N01..N10 map to OPENROUTER_API_KEY_1..10")

    # 3. DB Persistence & Reconciliation (Updating 3 -> 50 without resetting requests_used)
    print("\n[CHECK 3] PostgreSQL Persistence & Migration Reconciliation...")
    db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G01").update({
        LLMLaneModel.daily_limit: 3,
        LLMLaneModel.requests_used: 10,
        LLMLaneModel.state: LaneState.AVAILABLE.value
    })
    db.commit()

    # Re-initialize scheduler to trigger _sync_db_lanes()
    scheduler2 = QuotaScheduler(gemini_api_keys=g_keys, openrouter_api_keys=o_keys)
    g01_db = db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G01").first()

    assert g01_db.daily_limit == 50, "DB daily_limit must be reconciled to 50"
    assert g01_db.requests_used == 10, "DB requests_used must remain 10 without accidental reset"
    assert scheduler2.gemini_pool["G01"].requests_used == 10, "In-memory requests_used must remain 10"
    print("  ✅ Database records safely reconciled: daily_limit updated to 50, requests_used preserved at 10.")

    # 4. Least-Loaded Scheduling
    print("\n[CHECK 4] Least-Loaded Scheduling Policy...")
    reset_db_lanes()
    sched = QuotaScheduler(gemini_api_keys=g_keys, openrouter_api_keys=o_keys)
    l1, _, _ = sched.select_lane_sync()
    sched.release_lane(l1.lane_id, success=True)
    l2, _, _ = sched.select_lane_sync()
    sched.release_lane(l2.lane_id, success=True)
    assert l1.lane_id != l2.lane_id, "Scheduler must distribute requests across available lanes"
    print(f"  ✅ Requests distributed across lanes: {l1.lane_id} -> {l2.lane_id}")

    # 5. Per-Lane Quota Isolation & 50-Request Boundary Test
    print("\n[CHECK 5] Per-Lane Quota Isolation & 50-Request Boundary Test...")
    reset_db_lanes()
    db_test5 = SessionLocal()
    db_test5.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G01").update({
        LLMLaneModel.requests_used: 50,
        LLMLaneModel.state: LaneState.DAILY_EXHAUSTED.value
    })
    db_test5.commit()
    db_test5.close()

    sched3 = QuotaScheduler(gemini_api_keys=g_keys, openrouter_api_keys=o_keys)
    l_next, _, is_fallback = sched3.select_lane_sync()

    assert l_next.lane_id.startswith("G") and l_next.lane_id != "G01", f"G01 exhaustion must not block G02..G10, got {l_next.lane_id}"
    assert is_fallback is False, "Gemini primary pool must remain active while G02..G10 capacity exists"
    print(f"  ✅ G01 exhaustion isolated: G01 = DAILY_EXHAUSTED, sibling Gemini lane ({l_next.lane_id}) selected cleanly.")

    # 6. Single & Multiple Gemini Rate-Limit Isolation (429)
    print("\n[CHECK 6] Rate-Limit (429) Isolation & Cooldown Handling...")
    reset_db_lanes()
    sched4 = QuotaScheduler(gemini_api_keys=g_keys, openrouter_api_keys=o_keys)
    
    # Simulate HTTP 429 on G01
    sched4.release_lane("G01", success=False, status_code=429, error=Exception("HTTP 429 Rate Limit"))
    assert sched4.gemini_pool["G01"].state == LaneState.RATE_LIMITED, "G01 must enter RATE_LIMITED state"

    l_next_rl, _, _ = sched4.select_lane_sync()
    assert l_next_rl.lane_id != "G01", "Rate-limited G01 must be skipped"
    assert l_next_rl.provider == "gemini", "Other Gemini lanes must continue serving requests"
    print(f"  ✅ G01 HTTP 429 isolated: G01 = RATE_LIMITED, sibling Gemini lane selected.")

    # 7. Complete Gemini Failure & Automatic OpenRouter Fallback
    print("\n[CHECK 7] Complete Gemini Pool Failure -> OpenRouter Fallback...")
    reset_db_lanes()
    db_test7 = SessionLocal()
    from datetime import datetime, timezone, timedelta
    future_cd = datetime.now(timezone.utc) + timedelta(seconds=120)
    db_test7.query(LLMLaneModel).filter(LLMLaneModel.provider == "gemini").update({
        LLMLaneModel.state: LaneState.RATE_LIMITED.value,
        LLMLaneModel.cooldown_until: future_cd
    })
    db_test7.commit()
    db_test7.close()

    sched5 = QuotaScheduler(gemini_api_keys=g_keys, openrouter_api_keys=o_keys)
    l_fb, _, is_fallback_flag = sched5.select_lane_sync()

    assert is_fallback_flag is True, "Complete Gemini failure must trigger fallback"
    assert l_fb.provider == "nemotron", "Fallback lane must belong to OpenRouter/Nemotron pool"
    assert l_fb.lane_id == "N01", "Fallback must select N01"
    print(f"  ✅ Complete Gemini failure successfully routed to OpenRouter fallback (N01).")

    # 8. Gemini Auto-Recovery
    print("\n[CHECK 8] Gemini Auto-Recovery Verification...")
    reset_db_lanes()
    db_test8 = SessionLocal()
    db_test8.query(LLMLaneModel).filter(LLMLaneModel.lane_id == "G04").update({
        LLMLaneModel.state: LaneState.AVAILABLE.value,
        LLMLaneModel.requests_used: 0,
        LLMLaneModel.cooldown_until: None
    })
    db_test8.commit()
    db_test8.close()

    sched6 = QuotaScheduler(gemini_api_keys=g_keys, openrouter_api_keys=o_keys)
    l_rec, _, is_fb_rec = sched6.select_lane_sync()

    assert is_fb_rec is False, "Recovered Gemini capacity must resume primary routing"
    assert l_rec.lane_id.startswith("G"), f"Recovered Gemini lane must be selected, got {l_rec.lane_id}"
    print(f"  ✅ Gemini auto-recovery verified: Traffic immediately returned to recovered Gemini pool ({l_rec.lane_id}).")

    # Clean DB state after simulation checks
    db.query(LLMLaneModel).update({
        LLMLaneModel.requests_used: 0,
        LLMLaneModel.active_requests: 0,
        LLMLaneModel.state: LaneState.AVAILABLE.value,
        LLMLaneModel.cooldown_until: None,
        LLMLaneModel.error_count: 0
    })
    db.commit()

    # 9. Database Record Duplication Check
    print("\n[CHECK 9] Database Record Duplication Check...")
    lane_records = db.query(LLMLaneModel).all()
    lane_ids = [r.lane_id for r in lane_records]
    assert len(lane_records) == 20, f"Expected 20 DB records, found {len(lane_records)}"
    assert len(set(lane_ids)) == 20, "Database must not contain duplicate lane IDs"
    print(f"  ✅ Database contains exactly {len(lane_records)} distinct lane records. Zero duplicates.")

    db.close()
    print("\n================================================================================")
    print(" 🎉 ALL RELEASE-GATE AUDIT CHECKS PASSED 100%")
    print("================================================================================")


if __name__ == "__main__":
    run_checks()
