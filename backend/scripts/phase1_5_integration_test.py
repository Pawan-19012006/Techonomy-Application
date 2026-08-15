"""Phase 1.5 Scheduler Integration Test with Mocked LLM Providers."""

import asyncio
import sys
import time
from unittest.mock import AsyncMock

from app.knowledge.rag.llm_gateway import LLMGateway
from app.knowledge.rag.providers import LLMProvider
from app.knowledge.rag.scheduler import QuotaScheduler


async def run_phase1_5_test():
    print("=" * 80)
    print(" 🧪 TECHONOMY PHASE 1.5 SCHEDULER INTEGRATION TEST (MOCKED PROVIDERS)")
    print("=" * 80)

    # 1. Initialize QuotaScheduler with 10 Gemini lanes, 10 Nemotron lanes, test limit 3, max concurrency 1
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
        await asyncio.sleep(0.05)
        return f"Mocked Gemini answer for: {prompt}"

    mock_gemini_adapter.generate_async.side_effect = mock_gemini_generate_async

    mock_nemotron_adapter = AsyncMock(spec=LLMProvider)
    mock_nemotron_adapter.generate_async.return_value = "Mocked Nemotron answer"

    gateway = LLMGateway(
        scheduler=scheduler,
        gemini_adapter=mock_gemini_adapter,
        nemotron_adapter=mock_nemotron_adapter,
    )

    # 3. Send 10 concurrent requests
    async def send_request(req_id: int):
        prompt = f"Question {req_id}"
        result = await gateway.generate_async(prompt)
        return req_id, result

    print("Sending 10 concurrent mocked generation requests...")
    tasks = [send_request(i) for i in range(1, 11)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 4. Verifications
    failures = []

    successful_results = [r for r in results if isinstance(r, tuple)]
    if len(successful_results) != 10:
        failures.append(f"Verification 1 Failed: Expected 10 successful requests, got {len(successful_results)} (Errors: {[r for r in results if isinstance(r, Exception)]})")

    status = scheduler.get_status()
    metrics = status["metrics"]

    if metrics["gemini_requests"] != 10:
        failures.append(f"Verification 2 Failed: Expected 10 Gemini requests, got {metrics['gemini_requests']}")

    if metrics["nemotron_fallback_requests"] != 0:
        failures.append(f"Verification 3 Failed: Expected 0 Nemotron fallback requests, got {metrics['nemotron_fallback_requests']}")

    used_lanes = [l["lane_id"] for l in status["gemini"]["lanes"] if l["requests_used"] > 0]
    if len(used_lanes) != 10:
        failures.append(f"Verification 4 Failed: Expected 10 distinct Gemini lanes used, got {len(used_lanes)} ({used_lanes})")

    for l in status["gemini"]["lanes"]:
        if l["active_requests"] > 1:
            failures.append(f"Verification 5 Failed: Lane {l['lane_id']} had active_requests > 1 ({l['active_requests']})")

    for l in status["gemini"]["lanes"]:
        if l["requests_used"] > 3:
            failures.append(f"Verification 6 Failed: Lane {l['lane_id']} exceeded test limit 3 (used: {l['requests_used']})")

    for pool_name, pool in [("Gemini", status["gemini"]), ("Nemotron", status["nemotron"])]:
        for l in pool["lanes"]:
            if l["active_requests"] != 0:
                failures.append(f"Verification 7 Failed: {pool_name} lane {l['lane_id']} has active_requests={l['active_requests']} (expected 0)")

    print("\n" + "=" * 80)
    print(" VERIFICATION RESULTS")
    print("=" * 80)

    verifications = [
        ("1. All 10 requests succeed", len(successful_results) == 10),
        ("2. All 10 requests use Gemini", metrics["gemini_requests"] == 10),
        ("3. Nemotron receives 0 requests", metrics["nemotron_fallback_requests"] == 0),
        ("4. Requests distributed across Gemini lanes", len(used_lanes) == 10),
        ("5. No Gemini lane has active_requests > 1", all(l["active_requests"] <= 1 for l in status["gemini"]["lanes"])),
        ("6. No Gemini lane exceeds test limit (3)", all(l["requests_used"] <= 3 for l in status["gemini"]["lanes"])),
        ("7. All lanes return to active_requests = 0", all(l["active_requests"] == 0 for l in status["gemini"]["lanes"] + status["nemotron"]["lanes"])),
    ]

    for name, passed in verifications:
        symbol = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {symbol}: {name}")

    if failures:
        print("\n❌ FAILURES DETECTED:")
        for f in failures:
            print(f"  - {f}")
    else:
        print("\n✅ ALL 7 VERIFICATIONS PASSED CLEANLY")

    # 8. Print Concise Table
    print("\n" + "=" * 80)
    print(" GEMINI LANES STATUS TABLE")
    print("=" * 80)
    print(f"{'lane_id':<10} | {'requests_used':<15} | {'requests_remaining':<18} | {'final_state':<12}")
    print("-" * 65)
    for l in status["gemini"]["lanes"]:
        print(f"{l['lane_id']:<10} | {l['requests_used']:<15} | {l['requests_remaining']:<18} | {l['state']:<12}")
    print("-" * 65)

    return len(failures) == 0


if __name__ == "__main__":
    success = asyncio.run(run_phase1_5_test())
    sys.exit(0 if success else 1)
