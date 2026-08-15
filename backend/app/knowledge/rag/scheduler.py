"""Quota Scheduler managing Gemini Primary and Nemotron Fallback lane pools with PostgreSQL persistence."""

import asyncio
from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import case, or_, update
from sqlalchemy.orm import Session

from app.config import settings
from app.database.models import LLMLaneModel, utc_now
from app.database.db import SessionLocal
from app.knowledge.exceptions import LLMQuotaExhaustedError
from app.knowledge.rag.lane import LLMLane, LanePriority, LaneState
from app.utils.logging import logger


class QuotaScheduler:
    """Production Quota Scheduler managing Gemini primary and Nemotron fallback lane pools with PostgreSQL atomic persistence."""

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
        """Initializes QuotaScheduler with Gemini and Nemotron lane pools and synchronizes PostgreSQL persistence."""
        self._async_lock = asyncio.Lock()
        self.cooldown_seconds = cooldown_seconds

        # Credential map storing physical references without exposing raw keys in logs or DB
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

        # Build in-memory Gemini Primary Pool (G01..G10)
        self.gemini_pool: Dict[str, LLMLane] = {}
        for i in range(1, gemini_num_lanes + 1):
            lane_id = f"G{i:02d}"
            self.gemini_pool[lane_id] = LLMLane(
                lane_id=lane_id,
                provider="gemini",
                model=gemini_model,
                credential_ref="GEMINI_API_KEY",
                enabled=gemini_enabled and bool(gemini_api_key and gemini_api_key.strip()),
                priority=LanePriority.PRIMARY,
                max_concurrent_requests=gemini_max_concurrency,
                configured_test_request_limit=gemini_test_limit,
            )

        # Build in-memory Nemotron Fallback Pool (N01..N10)
        self.nemotron_pool: Dict[str, LLMLane] = {}
        for i in range(1, nemotron_num_lanes + 1):
            lane_id = f"N{i:02d}"
            self.nemotron_pool[lane_id] = LLMLane(
                lane_id=lane_id,
                provider="nemotron",
                model=nemotron_model,
                credential_ref="OPENROUTER_API_KEY",
                enabled=nemotron_enabled and bool(nemotron_api_key and nemotron_api_key.strip()),
                priority=LanePriority.FALLBACK,
                max_concurrent_requests=nemotron_max_concurrency,
                configured_test_request_limit=nemotron_test_limit,
            )

        # Synchronize PostgreSQL database tables and reconcile existing persistent counters
        self._sync_db_lanes()

    def _sync_db_lanes(self, db: Optional[Session] = None) -> None:
        """Ensures all lane records exist in PostgreSQL and reconciles in-memory lane state from DB."""
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            db_lanes = {l.lane_id: l for l in db.query(LLMLaneModel).all()}

            # Synchronize Gemini pool
            has_changes = False
            for lane_id, lane in self.gemini_pool.items():
                if lane_id not in db_lanes:
                    db_model = LLMLaneModel(
                        lane_id=lane_id,
                        provider=lane.provider,
                        model=lane.model,
                        credential_ref=lane.credential_ref,
                        enabled=lane.enabled,
                        priority=int(lane.priority),
                        daily_limit=lane.configured_test_request_limit,
                        max_concurrent_requests=lane.max_concurrent_requests,
                        requests_used=lane.requests_used,
                        active_requests=lane.active_requests,
                        state=lane.state.value,
                        cooldown_until=None,
                        error_count=lane.error_count,
                        created_at=utc_now(),
                        updated_at=utc_now(),
                    )
                    db.add(db_model)
                    has_changes = True
                else:
                    rec = db_lanes[lane_id]
                    if rec.enabled != lane.enabled or rec.model != lane.model:
                        rec.enabled = lane.enabled
                        rec.model = lane.model
                        has_changes = True
                    lane.requests_used = rec.requests_used
                    lane.active_requests = rec.active_requests
                    lane.error_count = rec.error_count
                    lane.state = LaneState(rec.state) if rec.state in LaneState.__members__ else LaneState.AVAILABLE
                    if rec.cooldown_until:
                        lane.cooldown_until = rec.cooldown_until.timestamp()

            # Synchronize Nemotron pool
            for lane_id, lane in self.nemotron_pool.items():
                if lane_id not in db_lanes:
                    db_model = LLMLaneModel(
                        lane_id=lane_id,
                        provider=lane.provider,
                        model=lane.model,
                        credential_ref=lane.credential_ref,
                        enabled=lane.enabled,
                        priority=int(lane.priority),
                        daily_limit=lane.configured_test_request_limit,
                        max_concurrent_requests=lane.max_concurrent_requests,
                        requests_used=lane.requests_used,
                        active_requests=lane.active_requests,
                        state=lane.state.value,
                        cooldown_until=None,
                        error_count=lane.error_count,
                        created_at=utc_now(),
                        updated_at=utc_now(),
                    )
                    db.add(db_model)
                    has_changes = True
                else:
                    rec = db_lanes[lane_id]
                    if rec.enabled != lane.enabled or rec.model != lane.model:
                        rec.enabled = lane.enabled
                        rec.model = lane.model
                        has_changes = True
                    lane.requests_used = rec.requests_used
                    lane.active_requests = rec.active_requests
                    lane.error_count = rec.error_count
                    lane.state = LaneState(rec.state) if rec.state in LaneState.__members__ else LaneState.AVAILABLE
                    if rec.cooldown_until:
                        lane.cooldown_until = rec.cooldown_until.timestamp()

            if has_changes:
                try:
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.debug(f"[SCHEDULER DB SYNC RETRY] Concurrent lane insertion conflict: {e}")
        except Exception as e:
            logger.error(f"[SCHEDULER DB SYNC ERROR] Failed to sync DB lanes: {e}")
            db.rollback()
        finally:
            if should_close:
                db.close()

    def get_api_key_for_lane(self, lane: LLMLane) -> str:
        """Returns the physical API key value associated with a lane's credential reference."""
        return self._credentials.get(lane.credential_ref, "")

    def _try_reserve_lane_db(self, lane: LLMLane, now_ts: float, db: Session) -> bool:
        """Attempts atomic SQL UPDATE reservation on PostgreSQL for a target lane."""
        now_dt = datetime.fromtimestamp(now_ts, timezone.utc)

        stmt = (
            update(LLMLaneModel)
            .where(
                LLMLaneModel.lane_id == lane.lane_id,
                LLMLaneModel.enabled.is_(True),
                LLMLaneModel.requests_used < LLMLaneModel.daily_limit,
                LLMLaneModel.active_requests < LLMLaneModel.max_concurrent_requests,
                or_(
                    LLMLaneModel.cooldown_until.is_(None),
                    LLMLaneModel.cooldown_until <= now_dt,
                ),
            )
            .values(
                requests_used=LLMLaneModel.requests_used + 1,
                active_requests=LLMLaneModel.active_requests + 1,
                state=case(
                    (LLMLaneModel.requests_used + 1 >= LLMLaneModel.daily_limit, LaneState.DAILY_EXHAUSTED.value),
                    (LLMLaneModel.active_requests + 1 >= LLMLaneModel.max_concurrent_requests, LaneState.BUSY.value),
                    else_=LLMLaneModel.state,
                ),
                cooldown_until=None,
                updated_at=utc_now(),
            )
        )

        try:
            res = db.execute(stmt)
            db.commit()
            if res.rowcount == 1:
                return True
        except Exception as e:
            db.rollback()
            logger.debug(f"[DB_LANE_RESERVE_RETRY] Database transaction conflict on lane '{lane.lane_id}': {e}")
            return False

        return False

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
        """Internal deterministic least-loaded lane selection logic backed by PostgreSQL atomic reservations."""
        t = now if now is not None else time.time()
        db = SessionLocal()

        try:
            # Reconcile in-memory pool with DB
            self._sync_db_lanes(db=db)

            # Step 1: Check Gemini Primary Pool Candidates
            gemini_candidates = [l for l in self.gemini_pool.values() if l.is_eligible(now=t)]
            gemini_candidates.sort(key=lambda l: (l.active_requests, l.requests_used, l.lane_id))

            for lane in gemini_candidates:
                if self._try_reserve_lane_db(lane, t, db):
                    self.total_requests += 1
                    self.gemini_requests += 1
                    api_key = self.get_api_key_for_lane(lane)
                    return lane, api_key, False

            # Step 2: Check Nemotron Fallback Pool Candidates
            nemotron_candidates = [l for l in self.nemotron_pool.values() if l.is_eligible(now=t)]
            nemotron_candidates.sort(key=lambda l: (l.active_requests, l.requests_used, l.lane_id))

            for lane in nemotron_candidates:
                if self._try_reserve_lane_db(lane, t, db):
                    self.total_requests += 1
                    self.nemotron_fallback_requests += 1
                    api_key = self.get_api_key_for_lane(lane)
                    return lane, api_key, True

            # Step 3: All pools exhausted
            if not self._credentials.get("GEMINI_API_KEY") and not self._credentials.get("OPENROUTER_API_KEY"):
                from app.knowledge.exceptions import OpenRouterAPIError
                raise OpenRouterAPIError("API key is missing. OPENROUTER_API_KEY environment variable must be configured.")

            raise LLMQuotaExhaustedError(
                "All LLM capacity pools (Gemini primary and Nemotron fallback) are currently exhausted or unavailable."
            )
        finally:
            db.close()

    def release_lane(
        self,
        lane_id: str,
        success: bool = True,
        status_code: Optional[int] = None,
        error: Optional[Exception] = None,
        now: Optional[float] = None,
    ) -> None:
        """Releases an active slot on the specified lane and updates persistent database state and operational metrics."""
        now_ts = now if now is not None else time.time()
        now_dt = datetime.fromtimestamp(now_ts, timezone.utc)

        db = SessionLocal()
        try:
            rec = db.query(LLMLaneModel).filter(LLMLaneModel.lane_id == lane_id).first()
            if rec:
                rec.active_requests = max(0, rec.active_requests - 1)
                if success:
                    rec.error_count = 0
                    if rec.requests_used >= rec.daily_limit:
                        rec.state = LaneState.DAILY_EXHAUSTED.value
                    elif rec.active_requests >= rec.max_concurrent_requests:
                        rec.state = LaneState.BUSY.value
                    else:
                        rec.state = LaneState.AVAILABLE.value
                else:
                    rec.error_count += 1
                    rec.last_error_time = now_dt
                    err_str = str(error).lower() if error else ""

                    if status_code == 429 or "429" in err_str or "rate limit" in err_str:
                        rec.state = LaneState.RATE_LIMITED.value
                        rec.cooldown_until = datetime.fromtimestamp(now_ts + self.cooldown_seconds, timezone.utc)
                    elif rec.error_count >= 3:
                        rec.state = LaneState.DEGRADED.value
                        rec.cooldown_until = datetime.fromtimestamp(now_ts + self.cooldown_seconds, timezone.utc)
                    elif rec.requests_used >= rec.daily_limit:
                        rec.state = LaneState.DAILY_EXHAUSTED.value
                    else:
                        rec.state = LaneState.AVAILABLE.value

                rec.updated_at = utc_now()
                db.commit()

            # Also release slot on in-memory domain model for local consistency
            lane = self.gemini_pool.get(lane_id) or self.nemotron_pool.get(lane_id)
            if lane:
                lane.release_slot(
                    success=success,
                    status_code=status_code,
                    error=error,
                    cooldown_seconds=self.cooldown_seconds,
                    now=now_ts,
                )

            if success:
                self.success_count += 1
            else:
                self.failure_count += 1

        except Exception as e:
            logger.error(f"[SCHEDULER RELEASE ERROR] Error releasing lane '{lane_id}': {e}")
            db.rollback()
        finally:
            db.close()

    def get_status(self) -> Dict[str, Any]:
        """Generates comprehensive status telemetry from persistent PostgreSQL state."""
        db = SessionLocal()
        try:
            db_lanes = {l.lane_id: l for l in db.query(LLMLaneModel).all()}
            now_ts = time.time()

            def summarize_pool(pool: Dict[str, LLMLane]) -> Dict[str, Any]:
                total = len(pool)
                available = 0
                busy = 0
                exhausted = 0
                rate_limited = 0
                degraded = 0
                disabled = 0

                total_configured_limit = 0
                total_requests_used = 0
                total_active_requests = 0
                lane_summaries = []

                for lid, in_mem in pool.items():
                    rec = db_lanes.get(lid)
                    req_used = rec.requests_used if rec else in_mem.requests_used
                    active_req = rec.active_requests if rec else in_mem.active_requests
                    limit = rec.daily_limit if rec else in_mem.configured_test_request_limit
                    state_str = rec.state if rec else in_mem.state.value

                    # Check cooldown expiry for telemetry status
                    if rec and rec.cooldown_until:
                        if now_ts < rec.cooldown_until.timestamp():
                            state_str = rec.state
                        else:
                            if req_used < limit:
                                state_str = LaneState.AVAILABLE.value

                    if state_str == LaneState.AVAILABLE.value:
                        available += 1
                    elif state_str == LaneState.BUSY.value:
                        busy += 1
                    elif state_str == LaneState.DAILY_EXHAUSTED.value:
                        exhausted += 1
                    elif state_str == LaneState.RATE_LIMITED.value:
                        rate_limited += 1
                    elif state_str == LaneState.DEGRADED.value:
                        degraded += 1
                    else:
                        disabled += 1

                    total_configured_limit += limit
                    total_requests_used += req_used
                    total_active_requests += active_req

                    lane_summaries.append({
                        "lane_id": lid,
                        "state": state_str,
                        "requests_used": req_used,
                        "requests_remaining": max(0, limit - req_used),
                        "active_requests": active_req,
                    })

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
                    "lanes": lane_summaries,
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
        finally:
            db.close()
