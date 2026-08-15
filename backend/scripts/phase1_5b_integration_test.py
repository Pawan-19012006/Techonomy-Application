"""Phase 1.5B Gemini Pool Exhaustion Test with Mocked LLM Providers."""

import asyncio
import sys
from unittest.mock import AsyncMock

from app.knowledge.rag.lane import LaneState
from app.knowledge.rag.llm_gateway import LLMGateway
from app.knowledge.rag.providers import LLMProvider
from app.knowledge.rag.scheduler import QuotaScheduler


async def run_phase1_5b_test():
    print("=" * 80)
    print(" 🧪 TECHONOMY PHASE 1.5B GEMINI POOL EXHAUSTION TEST (MOCKED PROVIDERS)")
    print("=" * 80)

    # 1. Initialize QuotaScheduler: 10 Gemini, 10 Nemotron, 3 test requests per lane, max concurrency = 1
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

    # 2. Setup Mock Provider Adapters (No real API calls!)
    mock_gemini_adapter = AsyncMock(spec=LLMProvider)
    
    async def mock_gemini_generate_async(prompt, model, api_key, timeout_seconds, max_retries, max_tokens):
        await asyncio.sleep(0)
        return f"Mocked Gemini answer for: {prompt}"

    mock_gemini_adapter.generate_async.side_effect = mock_gemini_generate_async

    mock_nemotron_adapter = AsyncMock(spec=LLMProvider)
    mock_nemotron_adapter.generate_async.return_value = "Mocked Nemotron answer"

    gateway = LLMGateway(
        scheduler=scheduler,
        gemini_adapter=mock_gemini_adapter,
        nemotron_adapter=mock_nemotron_adapter,
    )

    # 3. Send 30 mocked requests across 3 waves of 10 concurrent requests
    async def send_request(req_id: int):
        prompt = f"Exhaustion Test Question {req_id}"
        result = await gateway.generate_async(prompt)
        return req_id, result

    print("Sending 30 mocked generation requests across 3 waves of 10 concurrent requests...")
    results = []
    for wave in range(3):
        tasks = [send_request(wave * 10 + i) for i in range(1, 11)]
        wave_results = await asyncio.gather(*tasks, return_exceptions=True)
        results.extend(wave_results)

    # 4. Verifications
    failures = []

    successful_results = [r for r in results if isinstance(r, tuple)]
    if len(successful_results) != 30:
        failures.append(f"Verification 1 Failed: Expected 30 successful requests, got {len(successful_results)} (Errors: {[r for r in results if isinstance(r, Exception)]})")

    status = scheduler.get_status()
    metrics = status["metrics"]

    if metrics["gemini_requests"] != 30:
        failures.append(f"Verification 2 Failed: Expected 30 Gemini requests, got {metrics['gemini_requests']}")

    if metrics["nemotron_fallback_requests"] != 0:
        failures.append(f"Verification 3 Failed: Expected 0 Nemotron fallback requests, got {metrics['nemotron_fallback_requests']}")

    gemini_lanes = status["gemini"]["lanes"]
    nemotron_lanes = status["nemotron"]["lanes"]

    for l in gemini_lanes:
        if l["requests_used"] != 3:
            failures.append(f"Verification 4 Failed: Gemini lane {l['lane_id']} requests_used={l['requests_used']} (expected 3)")
        if l["requests_remaining"] != 0:
            failures.append(f"Verification 5 Failed: Gemini lane {l['lane_id']} requests_remaining={l['requests_remaining']} (expected 0)")

    for l in gemini_lanes:
        if l["active_requests"] > 1:
            failures.append(f"Verification 6 Failed: Gemini lane {l['lane_id']} active_requests={l['active_requests']} (expected <= 1)")

    for pool_name, pool in [("Gemini", status["gemini"]), ("Nemotron", status["nemotron"])]:
        for l in pool["lanes"]:
            if l["active_requests"] != 0:
                failures.append(f"Verification 7 Failed: {pool_name} lane {l['lane_id']} active_requests={l['active_requests']} (expected 0)")

    for l in gemini_lanes:
        if l["state"] != LaneState.DAILY_EXHAUSTED.value:
            failures.append(f"Verification 8 Failed: Gemini lane {l['lane_id']} state={l['state']} (expected DAILY_EXHAUSTED)")

    print("\n" + "=" * 80)
    print(" VERIFICATION RESULTS")
    print("=" * 80)

    verifications = [
        ("1. All 30 requests succeed", len(successful_results) == 30),
        ("2. All 30 requests routed to Gemini", metrics["gemini_requests"] == 30),
        ("3. Nemotron receives 0 requests", metrics["nemotron_fallback_requests"] == 0),
        ("4. Every Gemini lane receives exactly 3 requests", all(l["requests_used"] == 3 for l in gemini_lanes)),
        ("5. Every Gemini lane reaches requests_remaining = 0", all(l["requests_remaining"] == 0 for l in gemini_lanes)),
        ("6. No Gemini lane exceeds active_requests = 1", all(l["active_requests"] <= 1 for l in gemini_lanes)),
        ("7. After completion, active_requests = 0 for all lanes", all(l["active_requests"] == 0 for l in gemini_lanes + nemotron_lanes)),
        ("8. All Gemini lanes report DAILY_EXHAUSTED state", all(l["state"] == LaneState.DAILY_EXHAUSTED.value for l in gemini_lanes)),
    ]

    for name, passed in verifications:
        symbol = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {symbol}: {name}")

    if failures:
        print("\n❌ FAILURES DETECTED:")
        for f in failures:
            print(f"  - {f}")
    else:
        print("\n✅ ALL 8 VERIFICATIONS PASSED CLEANLY")

    # 9. Print Final Status Tables
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
    success = asyncio.run(run_phase1_5b_test())
    sys.exit(0 if success else 1)
