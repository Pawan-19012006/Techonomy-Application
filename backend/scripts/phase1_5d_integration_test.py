"""Phase 1.5D Failure-Aware Gemini Lane Routing Test with Mocked LLM Providers."""

import asyncio
import sys
import time
from unittest.mock import AsyncMock, MagicMock
import httpx

from app.knowledge.rag.lane import LaneState
from app.knowledge.rag.llm_gateway import LLMGateway
from app.knowledge.rag.providers import LLMProvider
from app.knowledge.rag.scheduler import QuotaScheduler


async def run_phase1_5d_test():
    print("=" * 80)
    print(" 🧪 TECHONOMY PHASE 1.5D FAILURE-AWARE GEMINI LANE ROUTING TEST (MOCKED)")
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

    g01_called = False

    # 2. Setup Mock Provider Adapters
    mock_gemini_adapter = AsyncMock(spec=LLMProvider)
    async def mock_gemini_generate_async(prompt, model, api_key, timeout_seconds, max_retries, max_tokens):
        nonlocal g01_called
        if not g01_called:
            g01_called = True
            mock_res = MagicMock()
            mock_res.status_code = 429
            mock_req = MagicMock()
            raise httpx.HTTPStatusError("429 Rate Limit Exceeded", request=mock_req, response=mock_res)
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

    print("\nExecuting sequential mocked requests...")
    print("-" * 75)
    print(f"{'Req #':<6} | {'Provider':<9} | {'Lane':<6} | {'HTTP Status':<12} | {'Lane State Transition':<25}")
    print("-" * 75)

    for i in range(1, 11):
        g01_lane_before = scheduler.gemini_pool["G01"]
        state_before_g01 = g01_lane_before.state.value

        snap_before = scheduler.get_status()
        status_code = 200
        used_provider = None
        used_lane_id = None

        try:
            await gateway.generate_async(f"Failure Test Prompt {i}")
            snap_after = scheduler.get_status()
            status_code = 200

            for g_lane in snap_after["gemini"]["lanes"]:
                prev = next(l for l in snap_before["gemini"]["lanes"] if l["lane_id"] == g_lane["lane_id"])
                if g_lane["requests_used"] > prev["requests_used"]:
                    used_provider = "gemini"
                    used_lane_id = g_lane["lane_id"]
                    break

            if not used_provider:
                for n_lane in snap_after["nemotron"]["lanes"]:
                    prev = next(l for l in snap_before["nemotron"]["lanes"] if l["lane_id"] == n_lane["lane_id"])
                    if n_lane["requests_used"] > prev["requests_used"]:
                        used_provider = "nemotron"
                        used_lane_id = n_lane["lane_id"]
                        break

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            used_provider = "gemini"
            used_lane_id = "G01"

        g01_lane_after = scheduler.gemini_pool["G01"]
        state_after_g01 = g01_lane_after.state.value
        transition_str = f"{state_before_g01} -> {state_after_g01}" if state_before_g01 != state_after_g01 else state_after_g01

        request_trace.append({
            "req_num": i,
            "provider": used_provider,
            "lane_id": used_lane_id,
            "http_status": status_code,
            "g01_state": state_after_g01,
            "transition": transition_str,
        })

        print(f"{i:<6} | {used_provider:<9} | {used_lane_id:<6} | {status_code:<12} | {transition_str:<25}")

    print("-" * 75)

    # 4. Verifications & Required Assertions
    failures = []
    status = scheduler.get_status()
    metrics = status["metrics"]
    gemini_lanes = status["gemini"]["lanes"]
    nemotron_lanes = status["nemotron"]["lanes"]
    g01 = scheduler.gemini_pool["G01"]

    if request_trace[0]["lane_id"] != "G01":
        failures.append(f"Assertion 1 Failed: First request selected {request_trace[0]['lane_id']} (expected G01)")

    if g01.state != LaneState.RATE_LIMITED:
        failures.append(f"Assertion 2 Failed: G01 state = {g01.state.value} (expected RATE_LIMITED)")

    if g01.is_eligible():
        failures.append("Assertion 3 Failed: G01 is eligible during rate limit cooldown")

    g01_reselected = [r for r in request_trace[1:] if r["lane_id"] == "G01"]
    if g01_reselected:
        failures.append(f"Assertion 4 Failed: G01 was re-selected during cooldown on requests {[r['req_num'] for r in g01_reselected]}")

    g02_g10_requests = sum(l["requests_used"] for l in gemini_lanes if l["lane_id"] != "G01")
    if g02_g10_requests != 9:
        failures.append(f"Assertion 5 Failed: G02-G10 received {g02_g10_requests} requests (expected 9)")

    if metrics["nemotron_fallback_requests"] != 0:
        failures.append(f"Assertion 6 Failed: Nemotron received {metrics['nemotron_fallback_requests']} requests (expected 0)")

    if g01.active_requests != 0:
        failures.append(f"Assertion 7 Failed: G01 active_requests = {g01.active_requests} (expected 0)")

    if g01.error_count != 1:
        failures.append(f"Assertion 8 Failed: G01 error_count = {g01.error_count} (expected 1)")

    if g01.cooldown_until is None or g01.cooldown_until <= time.time():
        failures.append(f"Assertion 9 Failed: G01 cooldown_until = {g01.cooldown_until} (expected future timestamp)")

    if any(l["active_requests"] > 1 for l in gemini_lanes + nemotron_lanes):
        failures.append("Assertion 10 Failed: A lane exceeded max_concurrency = 1")

    if any(l["active_requests"] != 0 for l in gemini_lanes + nemotron_lanes):
        failures.append("Assertion 11 Failed: Not all active slots were released back to 0")

    print("\n" + "=" * 80)
    print(" ASSERTION RESULTS")
    print("=" * 80)

    assertions_list = [
        ("1. First request selected G01", request_trace[0]["lane_id"] == "G01"),
        ("2. G01 transitioned to RATE_LIMITED after 429", g01.state == LaneState.RATE_LIMITED),
        ("3. G01 is temporarily ineligible during cooldown", not g01.is_eligible()),
        ("4. Next requests 2-10 did NOT select G01", len(g01_reselected) == 0),
        ("5. Healthy Gemini lanes G02-G10 received requests", g02_g10_requests == 9),
        ("6. Nemotron received 0 requests", metrics["nemotron_fallback_requests"] == 0),
        ("7. G01 active_requests returned to 0", g01.active_requests == 0),
        ("8. G01 error_count incremented to 1", g01.error_count == 1),
        ("9. G01 has a valid future cooldown_until timestamp", g01.cooldown_until is not None and g01.cooldown_until > time.time()),
        ("10. No lane exceeded max_concurrency = 1", all(l["active_requests"] <= 1 for l in gemini_lanes + nemotron_lanes)),
        ("11. All active slots released to 0 after completion", all(l["active_requests"] == 0 for l in gemini_lanes + nemotron_lanes)),
    ]

    for name, passed in assertions_list:
        symbol = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {symbol}: {name}")

    if failures:
        print("\n❌ FAILURES DETECTED:")
        for f in failures:
            print(f"  - {f}")
    else:
        print("\n✅ ALL ASSERTIONS PASSED CLEANLY")

    # 12. Complete Lane State Tables
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
    success = asyncio.run(run_phase1_5d_test())
    sys.exit(0 if success else 1)
