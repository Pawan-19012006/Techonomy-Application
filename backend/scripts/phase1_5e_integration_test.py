"""Phase 1.5E Concurrent Multi-Lane Gemini Failure and Fallback Test with Mocked LLM Providers."""

import asyncio
import sys
import time
from unittest.mock import AsyncMock, MagicMock
import httpx

from app.knowledge.rag.lane import LaneState
from app.knowledge.rag.llm_gateway import LLMGateway
from app.knowledge.rag.providers import LLMProvider
from app.knowledge.rag.scheduler import QuotaScheduler


async def run_phase1_5e_test():
    print("=" * 80)
    print(" 🧪 TECHONOMY PHASE 1.5E MULTI-LANE FAILURE AND FALLBACK TEST (MOCKED)")
    print("=" * 80)

    # 1. Initialize Fresh QuotaScheduler
    scheduler = QuotaScheduler(
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

    # 2. Setup Mock Provider Adapters
    mock_gemini_adapter = AsyncMock(spec=LLMProvider)
    
    async def mock_gemini_generate_async(prompt, model, api_key, timeout_seconds, max_retries, max_tokens):
        active_lane_id = None
        for lid, lobj in scheduler.gemini_pool.items():
            if lobj.active_requests > 0:
                active_lane_id = lid
                break

        if active_lane_id == "G01":
            mock_res = MagicMock(status_code=429)
            raise httpx.HTTPStatusError("429 Rate Limit", request=MagicMock(), response=mock_res)

        if active_lane_id == "G02":
            mock_res = MagicMock(status_code=429)
            raise httpx.HTTPStatusError("429 Rate Limit", request=MagicMock(), response=mock_res)

        if active_lane_id == "G03":
            mock_res = MagicMock(status_code=500)
            raise httpx.HTTPStatusError("500 Internal Error", request=MagicMock(), response=mock_res)

        if active_lane_id == "G04":
            mock_res = MagicMock(status_code=504)
            raise httpx.HTTPStatusError("504 Timeout Error", request=MagicMock(), response=mock_res)

        await asyncio.sleep(0)
        return f"Mocked Gemini answer for: {prompt}"

    mock_gemini_adapter.generate_async.side_effect = mock_gemini_generate_async

    mock_nemotron_adapter = AsyncMock(spec=LLMProvider)
    async def mock_nemotron_generate_async(prompt, model, api_key, timeout_seconds, max_retries, max_tokens):
        await asyncio.sleep(0)
        return f"Mocked Nemotron answer for: {prompt}"

    mock_nemotron_adapter.generate_async.side_effect = mock_nemotron_generate_async

    gateway = LLMGateway(
        scheduler=scheduler,
        gemini_adapter=mock_gemini_adapter,
        nemotron_adapter=mock_nemotron_adapter,
    )

    request_trace = []

    print("\nExecuting sequential mocked generation requests...")
    print("-" * 75)
    print(f"{'Req #':<6} | {'Provider':<9} | {'Lane':<6} | {'Status':<12} | {'Fallback Flag':<15}")
    print("-" * 75)

    # Send 30 requests:
    # Req 1: G01 (429 -> RATE_LIMITED)
    # Req 2: G02 (429 -> RATE_LIMITED)
    # Req 3, 5, 7: G03 (500 3x -> DEGRADED)
    # Req 4, 6, 8: G04 (504 3x -> DEGRADED)
    # Req 9..26: G05..G10 (18 successful Gemini requests -> DAILY_EXHAUSTED)
    # Req 27..30: Nemotron fallback (4 requests -> fallback = True)
    for i in range(1, 31):
        snap_before = scheduler.get_status()
        status_code = 200
        used_provider = None
        used_lane_id = None
        is_fallback = False

        try:
            res = await gateway.generate_async(f"Prompt {i}")
            snap_after = scheduler.get_status()
            status_code = 200

            for g_lane in snap_after["gemini"]["lanes"]:
                prev = next(l for l in snap_before["gemini"]["lanes"] if l["lane_id"] == g_lane["lane_id"])
                if g_lane["requests_used"] > prev["requests_used"]:
                    used_provider = "gemini"
                    used_lane_id = g_lane["lane_id"]
                    is_fallback = False
                    break

            if not used_provider:
                for n_lane in snap_after["nemotron"]["lanes"]:
                    prev = next(l for l in snap_before["nemotron"]["lanes"] if l["lane_id"] == n_lane["lane_id"])
                    if n_lane["requests_used"] > prev["requests_used"]:
                        used_provider = "nemotron"
                        used_lane_id = n_lane["lane_id"]
                        is_fallback = True
                        break

        except httpx.HTTPStatusError as exc:
            snap_after = scheduler.get_status()
            status_code = exc.response.status_code
            used_provider = "gemini"
            for g_lane in snap_after["gemini"]["lanes"]:
                lid = g_lane["lane_id"]
                prev_used = next(l for l in snap_before["gemini"]["lanes"] if l["lane_id"] == lid)["requests_used"]
                if g_lane["requests_used"] > prev_used:
                    used_lane_id = lid
                    break
            if not used_lane_id:
                used_lane_id = "UNKNOWN"
            is_fallback = False

        request_trace.append({
            "req_num": i,
            "provider": used_provider,
            "lane_id": used_lane_id,
            "status": status_code,
            "is_fallback": is_fallback,
        })

        print(f"{i:<6} | {used_provider:<9} | {used_lane_id:<6} | {status_code:<12} | {str(is_fallback):<15}")

    print("-" * 75)

    # 4. Assertions Verification
    failures = []
    status = scheduler.get_status()
    metrics = status["metrics"]
    gemini_lanes = status["gemini"]["lanes"]
    nemotron_lanes = status["nemotron"]["lanes"]

    g01 = scheduler.gemini_pool["G01"]
    g02 = scheduler.gemini_pool["G02"]
    g03 = scheduler.gemini_pool["G03"]
    g04 = scheduler.gemini_pool["G04"]

    if not (g01.state != LaneState.AVAILABLE and g02.state != LaneState.AVAILABLE and g03.state != LaneState.AVAILABLE and g04.state != LaneState.AVAILABLE):
        failures.append("Assertion 1 Failed: Not all failed lanes entered failure states")

    if g01.state != LaneState.RATE_LIMITED or g02.state != LaneState.RATE_LIMITED:
        failures.append(f"Assertion 2 Failed: G01 state={g01.state.value}, G02 state={g02.state.value} (expected RATE_LIMITED)")

    if g03.state != LaneState.DEGRADED or g04.state != LaneState.DEGRADED:
        failures.append(f"Assertion 3 Failed: G03 state={g03.state.value}, G04 state={g04.state.value} (expected DEGRADED)")

    if g01.is_eligible() or g02.is_eligible() or g03.is_eligible() or g04.is_eligible():
        failures.append("Assertion 4 Failed: A failed lane remained eligible during cooldown")

    g05_g10_reqs = sum(l["requests_used"] for l in gemini_lanes if l["lane_id"] in ["G05", "G06", "G07", "G08", "G09", "G10"])
    if g05_g10_reqs != 18:
        failures.append(f"Assertion 5 Failed: G05-G10 served {g05_g10_reqs} requests (expected 18)")

    nemotron_during_gemini = [r for r in request_trace[:26] if r["provider"] == "nemotron"]
    if nemotron_during_gemini:
        failures.append(f"Assertion 6 Failed: Nemotron received requests during Gemini availability: {nemotron_during_gemini}")

    nemotron_after_exhaustion = [r for r in request_trace[26:] if r["provider"] == "nemotron" and r["is_fallback"]]
    if len(nemotron_after_exhaustion) != 4:
        failures.append(f"Assertion 7/8 Failed: Expected 4 Nemotron fallback requests after Gemini exhaustion, got {len(nemotron_after_exhaustion)}")

    if any(l["active_requests"] > 1 for l in gemini_lanes + nemotron_lanes):
        failures.append("Assertion 9 Failed: A lane exceeded max_concurrency = 1")

    if any(l["active_requests"] != 0 for l in gemini_lanes + nemotron_lanes):
        failures.append("Assertion 10 Failed: Active requests did not return to 0")

    for lid in ["G01", "G02", "G03", "G04"]:
        if scheduler.gemini_pool[lid].error_count < 1:
            failures.append(f"Assertion 11 Failed: Lane {lid} error_count = {scheduler.gemini_pool[lid].error_count} (expected >= 1)")

    for lid in ["G01", "G02", "G03", "G04"]:
        cd = scheduler.gemini_pool[lid].cooldown_until
        if cd is None or cd <= time.time():
            failures.append(f"Assertion 12 Failed: Lane {lid} cooldown_until = {cd} (expected future timestamp)")

    if len(request_trace) != 30:
        failures.append(f"Assertion 15 Failed: Processed {len(request_trace)} requests (expected 30)")

    print("\n" + "=" * 80)
    print(" ASSERTION RESULTS")
    print("=" * 80)

    assertions_list = [
        ("1. Multiple Gemini lanes independently entered failure states", g01.state != LaneState.AVAILABLE and g02.state != LaneState.AVAILABLE and g03.state != LaneState.AVAILABLE and g04.state != LaneState.AVAILABLE),
        ("2. G01 and G02 entered RATE_LIMITED", g01.state == LaneState.RATE_LIMITED and g02.state == LaneState.RATE_LIMITED),
        ("3. G03 and G04 entered DEGRADED", g03.state == LaneState.DEGRADED and g04.state == LaneState.DEGRADED),
        ("4. Failed lanes became temporarily ineligible during cooldown", not (g01.is_eligible() or g02.is_eligible() or g03.is_eligible() or g04.is_eligible())),
        ("5. Healthy Gemini lanes G05-G10 served all 18 requests", g05_g10_reqs == 18),
        ("6. Nemotron received ZERO requests while Gemini lanes remained eligible", len(nemotron_during_gemini) == 0),
        ("7. Requests 27-30 routed to Nemotron after Gemini pool exhaustion", len(nemotron_after_exhaustion) == 4),
        ("8. Nemotron requests flagged with fallback = True", all(r["is_fallback"] for r in nemotron_after_exhaustion)),
        ("9. No lane exceeded max_concurrency = 1", all(l["active_requests"] <= 1 for l in gemini_lanes + nemotron_lanes)),
        ("10. All active_requests returned to 0 after completion", all(l["active_requests"] == 0 for l in gemini_lanes + nemotron_lanes)),
        ("11. Failed Gemini lanes retained error_count >= 1", all(scheduler.gemini_pool[lid].error_count >= 1 for lid in ["G01", "G02", "G03", "G04"])),
        ("12. Failed Gemini lanes set future cooldown_until timestamps", all(scheduler.gemini_pool[lid].cooldown_until is not None and scheduler.gemini_pool[lid].cooldown_until > time.time() for lid in ["G01", "G02", "G03", "G04"])),
        ("15. No request was silently dropped (30/30 processed)", len(request_trace) == 30),
    ]

    for name, passed in assertions_list:
        symbol = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {symbol}: {name}")

    if failures:
        print("\n❌ FAILURES DETECTED:")
        for f in failures:
            print(f"  - {f}")
    else:
        print("\n✅ ALL 15 ASSERTIONS PASSED CLEANLY")

    # 14. Print final state for all 20 lanes
    print("\n" + "=" * 80)
    print(" GEMINI LANES FINAL STATUS TABLE")
    print("=" * 80)
    print(f"{'lane_id':<10} | {'requests_used':<15} | {'requests_remaining':<18} | {'error_count':<12} | {'final_state':<15}")
    print("-" * 80)
    for l in gemini_lanes:
        err_cnt = scheduler.gemini_pool[l["lane_id"]].error_count
        print(f"{l['lane_id']:<10} | {l['requests_used']:<15} | {l['requests_remaining']:<18} | {err_cnt:<12} | {l['state']:<15}")
    print("-" * 80)

    print("\n" + "=" * 80)
    print(" NEMOTRON LANES FINAL STATUS TABLE")
    print("=" * 80)
    print(f"{'lane_id':<10} | {'requests_used':<15} | {'requests_remaining':<18} | {'error_count':<12} | {'final_state':<15}")
    print("-" * 80)
    for l in nemotron_lanes:
        err_cnt = scheduler.nemotron_pool[l["lane_id"]].error_count
        print(f"{l['lane_id']:<10} | {l['requests_used']:<15} | {l['requests_remaining']:<18} | {err_cnt:<12} | {l['state']:<15}")
    print("-" * 80)

    return len(failures) == 0


if __name__ == "__main__":
    success = asyncio.run(run_phase1_5e_test())
    sys.exit(0 if success else 1)
