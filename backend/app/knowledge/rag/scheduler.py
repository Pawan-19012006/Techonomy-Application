"""Quota Scheduler managing Gemini Primary and Nemotron Fallback lane pools."""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple

from app.config import settings
from app.knowledge.exceptions import LLMQuotaExhaustedError
from app.knowledge.rag.lane import LLMLane, LanePriority, LaneState
from app.utils.logging import logger


class QuotaScheduler:
    """Production Quota Scheduler managing Gemini primary and Nemotron fallback lane pools with concurrency safety."""

    def __init__(
        self,
        gemini_api_key: str = settings.GEMINI_API_KEY,
        nemotron_api_key: str = settings.OPENROUTER_API_KEY,
        gemini_enabled: bool = settings.GEMINI_ENABLED,
        nemotron_enabled: bool = settings.NEMOTRON_ENABLED,
        gemini_model: str = settings.GEMINI_MODEL,
        nemotron_model: str = settings.PRIMARY_MODEL,
        gemini_test_limit: int = settings.GEMINI_TEST_REQUEST_LIMIT,
        nemotron_test_limit: int = settings.NEMOTRON_TEST_REQUEST_LIMIT,
        gemini_max_concurrency: int = settings.GEMINI_MAX_CONCURRENT_REQUESTS,
        nemotron_max_concurrency: int = settings.NEMOTRON_MAX_CONCURRENT_REQUESTS,
        gemini_num_lanes: int = settings.GEMINI_NUM_LANES,
        nemotron_num_lanes: int = settings.NEMOTRON_NUM_LANES,
        cooldown_seconds: float = settings.SCHEDULER_COOLDOWN_SECONDS,
    ):
        """Initializes QuotaScheduler with Gemini and Nemotron lane pools."""
        self._async_lock = asyncio.Lock()
        self.cooldown_seconds = cooldown_seconds

        # Credential map storing physical references without exposing raw keys in logs
        self._credentials: Dict[str, str] = {
            "GEMINI_API_KEY": gemini_api_key,
            "OPENROUTER_API_KEY": nemotron_api_key,
        }

        # Global scheduler operational statistics
        self.total_requests: int = 0
        self.gemini_requests: int = 0
        self.nemotron_fallback_requests: int = 0
        self.success_count: int = 0
        self.failure_count: int = 0

        # Build Gemini Primary Pool (G01..G10)
        self.gemini_pool: Dict[str, LLMLane] = {}
        for i in range(1, gemini_num_lanes + 1):
            lane_id = f"G{i:02d}"
            self.gemini_pool[lane_id] = LLMLane(
                lane_id=lane_id,
                provider="gemini",
                model=gemini_model,
                credential_ref="GEMINI_API_KEY",
                enabled=gemini_enabled and bool(gemini_api_key),
                priority=LanePriority.PRIMARY,
                max_concurrent_requests=gemini_max_concurrency,
                configured_test_request_limit=gemini_test_limit,
            )

        # Build Nemotron Fallback Pool (N01..N10)
        self.nemotron_pool: Dict[str, LLMLane] = {}
        for i in range(1, nemotron_num_lanes + 1):
            lane_id = f"N{i:02d}"
            self.nemotron_pool[lane_id] = LLMLane(
                lane_id=lane_id,
                provider="nemotron",
                model=nemotron_model,
                credential_ref="OPENROUTER_API_KEY",
                enabled=nemotron_enabled and bool(nemotron_api_key),
                priority=LanePriority.FALLBACK,
                max_concurrent_requests=nemotron_max_concurrency,
                configured_test_request_limit=nemotron_test_limit,
            )

    def get_api_key_for_lane(self, lane: LLMLane) -> str:
        """Returns the physical API key value associated with a lane's credential reference."""
        return self._credentials.get(lane.credential_ref, "")

    def _select_eligible_lane(self, pool: Dict[str, LLMLane], now: Optional[float] = None) -> Optional[LLMLane]:
        """Selects the eligible lane with the lowest load in a given pool."""
        eligible_lanes = [lane for lane in pool.values() if lane.is_eligible(now)]
        if not eligible_lanes:
            return None

        # Least-loaded selection: lowest active requests first, then lowest total requests used, then lane_id
        eligible_lanes.sort(key=lambda l: (l.active_requests, l.requests_used, l.lane_id))
        return eligible_lanes[0]

    async def select_lane_async(self, now: Optional[float] = None) -> Tuple[LLMLane, str, bool]:
        """Atomically evaluates capacity and selects an eligible lane under async lock.
        
        Returns: (lane, api_key, is_fallback)
        """
        async with self._async_lock:
            return self._select_lane_internal(now=now)

    def select_lane_sync(self, now: Optional[float] = None) -> Tuple[LLMLane, str, bool]:
        """Synchronously evaluates capacity and selects an eligible lane.
        
        Returns: (lane, api_key, is_fallback)
        """
        return self._select_lane_internal(now=now)

    def _select_lane_internal(self, now: Optional[float] = None) -> Tuple[LLMLane, str, bool]:
        """Internal deterministic least-loaded lane selection logic."""
        t = now if now is not None else time.time()

        # Step 1: Check Gemini Primary Pool
        selected_lane = self._select_eligible_lane(self.gemini_pool, now=t)
        if selected_lane is not None:
            selected_lane.reserve_slot()
            self.total_requests += 1
            self.gemini_requests += 1
            api_key = self.get_api_key_for_lane(selected_lane)
            return selected_lane, api_key, False

        # Step 2: Check Nemotron Fallback Pool
        selected_lane = self._select_eligible_lane(self.nemotron_pool, now=t)
        if selected_lane is not None:
            selected_lane.reserve_slot()
            self.total_requests += 1
            self.nemotron_fallback_requests += 1
            api_key = self.get_api_key_for_lane(selected_lane)
            return selected_lane, api_key, True

        # Step 3: All pools exhausted
        if not self._credentials.get("GEMINI_API_KEY") and not self._credentials.get("OPENROUTER_API_KEY"):
            from app.knowledge.exceptions import OpenRouterAPIError
            raise OpenRouterAPIError("API key is missing. OPENROUTER_API_KEY environment variable must be configured.")

        raise LLMQuotaExhaustedError(
            "All LLM capacity pools (Gemini primary and Nemotron fallback) are currently exhausted or unavailable."
        )

    def release_lane(
        self,
        lane_id: str,
        success: bool = True,
        status_code: Optional[int] = None,
        error: Optional[Exception] = None,
        now: Optional[float] = None,
    ) -> None:
        """Releases an active slot on the specified lane and updates operational metrics."""
        lane = self.gemini_pool.get(lane_id) or self.nemotron_pool.get(lane_id)
        if lane is None:
            logger.warning(f"[SCHEDULER WARNING] Attempted to release unknown lane_id '{lane_id}'.")
            return

        lane.release_slot(
            success=success,
            status_code=status_code,
            error=error,
            cooldown_seconds=self.cooldown_seconds,
            now=now,
        )

        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

    def get_status(self) -> Dict[str, Any]:
        """Generates comprehensive status telemetry for scheduler pools and operational counters."""
        def summarize_pool(pool: Dict[str, LLMLane]) -> Dict[str, Any]:
            total = len(pool)
            available = sum(1 for l in pool.values() if l.state == LaneState.AVAILABLE)
            busy = sum(1 for l in pool.values() if l.state == LaneState.BUSY)
            exhausted = sum(1 for l in pool.values() if l.state == LaneState.DAILY_EXHAUSTED)
            rate_limited = sum(1 for l in pool.values() if l.state == LaneState.RATE_LIMITED)
            degraded = sum(1 for l in pool.values() if l.state == LaneState.DEGRADED)
            disabled = sum(1 for l in pool.values() if l.state == LaneState.DISABLED or not l.enabled)

            total_configured_limit = sum(l.configured_test_request_limit for l in pool.values())
            total_requests_used = sum(l.requests_used for l in pool.values())
            total_active_requests = sum(l.active_requests for l in pool.values())

            return {
                "total_lanes": total,
                "available_lanes": available,
                "busy_lanes": busy,
                "exhausted_lanes": exhausted,
                "rate_limited_lanes": rate_limited,
                "degraded_lanes": degraded,
                "disabled_lanes": disabled,
                "total_configured_test_request_limit": total_configured_limit,
                "total_requests_used": total_requests_used,
                "total_active_requests": total_active_requests,
                "lanes": [
                    {
                        "lane_id": l.lane_id,
                        "state": l.state.value,
                        "requests_used": l.requests_used,
                        "requests_remaining": l.requests_remaining,
                        "active_requests": l.active_requests,
                    }
                    for l in pool.values()
                ],
            }

        return {
            "gemini": summarize_pool(self.gemini_pool),
            "nemotron": summarize_pool(self.nemotron_pool),
            "metrics": {
                "total_requests": self.total_requests,
                "gemini_requests": self.gemini_requests,
                "nemotron_fallback_requests": self.nemotron_fallback_requests,
                "success_count": self.success_count,
                "failure_count": self.failure_count,
            },
        }
