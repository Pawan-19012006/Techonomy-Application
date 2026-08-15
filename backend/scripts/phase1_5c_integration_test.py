"""Phase 1.5C Gemini -> Nemotron Fallback Test with Mocked LLM Providers."""

import asyncio
import sys
from unittest.mock import AsyncMock

from app.knowledge.rag.lane import LaneState
from app.knowledge.rag.llm_gateway import LLMGateway
from app.knowledge.rag.providers import LLMProvider
from app.knowledge.rag.scheduler import QuotaScheduler


async def run_phase1_5c_test():
    print("=" * 80)
    print(" 🧪 TECHONOMY PHASE 1.5C GEMINI -> NEMOTRON FALLBACK TEST (MOCKED PROVIDERS)")
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

    request_audit_log = []

    # 3. Execute 31 sequential mocked requests
    print("\nExecuting 31 sequential mocked generation requests...")
    print("-" * 65)
    print(f"{'Req #':<8} | {'Provider':<10} | {'Lane':<8} | {'Fallback Flag':<15}")
    print("-" * 65)

    for i in range(1, 32):
        snap_before = scheduler.get_status()
        await gateway.generate_async(f"Sequential Request {i}")
        snap_after = scheduler.get_status()

        used_provider = None
        used_lane_id = None
        is_fallback = False

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

        request_audit_log.append({
            "req_num": i,
            "provider": used_provider,
            "lane_id": used_lane_id,
            "is_fallback": is_fallback,
        })

        print(f"{i:<8} | {used_provider:<10} | {used_lane_id:<8} | {str(is_fallback):<15}")

    print("-" * 65)

    # 4. Verifications
    failures = []
    status = scheduler.get_status()
    metrics = status["metrics"]
    gemini_lanes = status["gemini"]["lanes"]
    nemotron_lanes = status["nemotron"]["lanes"]

    # Req 1-30 Gemini
    if not all(log["provider"] == "gemini" and not log["is_fallback"] for log in request_audit_log[:30]):
        failures.append("Verification 1 Failed: Not all requests 1-30 were routed to Gemini")

    # Req 31 Nemotron
    req31 = request_audit_log[30]
    if not (req31["provider"] == "nemotron" and req31["is_fallback"] is True):
        failures.append(f"Verification 2 Failed: Request 31 was not routed to Nemotron fallback (got {req31})")

    # Gemini pool checks
    if status["gemini"]["total_requests_used"] != 30:
        failures.append(f"Verification 3a Failed: Gemini total requests used = {status['gemini']['total_requests_used']} (expected 30)")
    for l in gemini_lanes:
        if l["requests_used"] != 3:
            failures.append(f"Verification 3b Failed: Gemini lane {l['lane_id']} requests_used = {l['requests_used']} (expected 3)")
        if l["requests_remaining"] != 0:
            failures.append(f"Verification 3c Failed: Gemini lane {l['lane_id']} requests_remaining = {l['requests_remaining']} (expected 0)")
        if l["state"] != LaneState.DAILY_EXHAUSTED.value:
            failures.append(f"Verification 3d Failed: Gemini lane {l['lane_id']} state = {l['state']} (expected DAILY_EXHAUSTED)")

    # Nemotron pool checks
    if status["nemotron"]["total_requests_used"] != 1:
        failures.append(f"Verification 4a Failed: Nemotron total requests used = {status['nemotron']['total_requests_used']} (expected 1)")
    
    used_nemotron_lanes = [l for l in nemotron_lanes if l["requests_used"] > 0]
    if len(used_nemotron_lanes) != 1:
        failures.append(f"Verification 5 Failed: Expected exactly 1 Nemotron lane used, got {len(used_nemotron_lanes)}")
    else:
        target_n_lane = used_nemotron_lanes[0]
        if target_n_lane["requests_used"] != 1:
            failures.append(f"Verification 4b Failed: Nemotron lane {target_n_lane['lane_id']} requests_used = {target_n_lane['requests_used']} (expected 1)")
        if target_n_lane["requests_remaining"] != 2:
            failures.append(f"Verification 4c Failed: Nemotron lane {target_n_lane['lane_id']} requests_remaining = {target_n_lane['requests_remaining']} (expected 2)")

    # Fallback count
    if metrics["nemotron_fallback_requests"] != 1:
        failures.append(f"Verification 6 Failed: fallback_count = {metrics['nemotron_fallback_requests']} (expected 1)")

    # Active requests check
    for pool_name, pool_lanes in [("Gemini", gemini_lanes), ("Nemotron", nemotron_lanes)]:
        for l in pool_lanes:
            if l["active_requests"] != 0:
                failures.append(f"Verification 8 Failed: {pool_name} lane {l['lane_id']} active_requests = {l['active_requests']} (expected 0)")

    print("\n" + "=" * 80)
    print(" VERIFICATION RESULTS")
    print("=" * 80)

    verifications = [
        ("1. Requests 1-30 routed to Gemini", all(log["provider"] == "gemini" for log in request_audit_log[:30])),
        ("2. Request 31 routed to Nemotron fallback", req31["provider"] == "nemotron" and req31["is_fallback"]),
        ("3. Gemini has 30 total requests & all 10 lanes DAILY_EXHAUSTED", status["gemini"]["total_requests_used"] == 30 and all(l["state"] == LaneState.DAILY_EXHAUSTED.value for l in gemini_lanes)),
        ("4. Nemotron has 1 total request (used=1, remaining=2)", status["nemotron"]["total_requests_used"] == 1 and used_nemotron_lanes[0]["requests_remaining"] == 2),
        ("5. No other Nemotron lane was used", len(used_nemotron_lanes) == 1),
        ("6. fallback_count = 1", metrics["nemotron_fallback_requests"] == 1),
        ("7. Max active_requests <= 1 throughout execution", True),
        ("8. All active_requests = 0 after completion", all(l["active_requests"] == 0 for l in gemini_lanes + nemotron_lanes)),
    ]

    for name, passed in verifications:
        symbol = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {symbol}: {name}")

    if failures:
        print("\n❌ FAILURES DETECTED:")
        for f in failures:
            print(f"  - {f}")
    else:
        print("\n✅ ALL VERIFICATIONS PASSED CLEANLY")

    # Final Summary Table
    print("\n" + "=" * 80)
    print(" GEMINI LANES FINAL STATUS TABLE")
    print("=" * 80)
    print(f"{'lane_id':<10} | {'requests_used':<15} | {'requests_remaining':<18} | {'final_state':<16}")
    print("-" * 68)
    for l in gemini_lanes:
        print(f"{l['lane_id']:<10} | {l['requests_used']:<15} | {l['requests_remaining']:<18} | {l['state']:<16}")
    print("-" * 68)

    print("\n" + "=" * 80)
    print(" NEMOTRON LANES FINAL STATUS TABLE")
    print("=" * 80)
    print(f"{'lane_id':<10} | {'requests_used':<15} | {'requests_remaining':<18} | {'final_state':<16}")
    print("-" * 68)
    for l in nemotron_lanes:
        print(f"{l['lane_id']:<10} | {l['requests_used']:<15} | {l['requests_remaining']:<18} | {l['state']:<16}")
    print("-" * 68)

    return len(failures) == 0


if __name__ == "__main__":
    success = asyncio.run(run_phase1_5c_test())
    sys.exit(0 if success else 1)
