"""LLM Lane abstraction and state machine for quota-aware scheduling."""

from enum import Enum
import time
from typing import Optional
from pydantic import BaseModel, Field


class LaneState(str, Enum):
    """Possible runtime operational states for an LLM lane."""
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    RATE_LIMITED = "RATE_LIMITED"
    DAILY_EXHAUSTED = "DAILY_EXHAUSTED"
    DEGRADED = "DEGRADED"
    DISABLED = "DISABLED"


class LanePriority(int, Enum):
    """Pool routing priority level."""
    PRIMARY = 1
    FALLBACK = 2


class LLMLane(BaseModel):
    """Domain model representing a single logical LLM execution lane."""

    lane_id: str = Field(..., description="Unique lane identifier e.g. G01, N01")
    provider: str = Field(..., description="Provider name e.g. gemini, nemotron")
    model: str = Field(..., description="Model identifier")
    credential_ref: str = Field(..., description="Reference key for credential lookup e.g. GEMINI_API_KEY")
    enabled: bool = Field(default=True, description="Whether lane is administrative enabled")
    priority: LanePriority = Field(default=LanePriority.PRIMARY, description="Pool routing priority")
    max_concurrent_requests: int = Field(default=1, description="Configured maximum active concurrent requests per lane")
    configured_test_request_limit: int = Field(default=3, description="Artificial test request limit for scheduling evaluation")
    requests_used: int = Field(default=0, description="Total requests reserved on this lane")
    active_requests: int = Field(default=0, description="Current in-flight active requests on this lane")
    state: LaneState = Field(default=LaneState.AVAILABLE, description="Current operational state of the lane")
    cooldown_until: Optional[float] = Field(default=None, description="Timestamp until which the lane is in cooldown")
    error_count: int = Field(default=0, description="Consecutive error count")
    last_error_time: Optional[float] = Field(default=None, description="Timestamp of most recent error")

    @property
    def requests_remaining(self) -> int:
        """Returns remaining test capacity slots for the lane."""
        return max(0, self.configured_test_request_limit - self.requests_used)

    def is_eligible(self, now: Optional[float] = None) -> bool:
        """Determines whether the lane can currently accept a new request."""
        t = now if now is not None else time.time()

        if not self.enabled or self.state == LaneState.DISABLED:
            return False

        # Auto-recover from cooldown if window has elapsed
        if self.cooldown_until is not None:
            if t >= self.cooldown_until:
                self.cooldown_until = None
                if self.requests_used < self.configured_test_request_limit:
                    self.state = LaneState.AVAILABLE
            else:
                return False

        if self.requests_used >= self.configured_test_request_limit:
            self.state = LaneState.DAILY_EXHAUSTED
            return False

        if self.active_requests >= self.max_concurrent_requests:
            self.state = LaneState.BUSY
            return False

        return self.state in (LaneState.AVAILABLE, LaneState.BUSY)

    def reserve_slot(self) -> None:
        """Reserves a capacity slot on this lane atomically."""
        self.requests_used += 1
        self.active_requests += 1

        if self.requests_used >= self.configured_test_request_limit:
            self.state = LaneState.DAILY_EXHAUSTED
        elif self.active_requests >= self.max_concurrent_requests:
            self.state = LaneState.BUSY

    def release_slot(
        self,
        success: bool = True,
        status_code: Optional[int] = None,
        error: Optional[Exception] = None,
        cooldown_seconds: float = 60.0,
        now: Optional[float] = None,
    ) -> None:
        """Releases an active request slot and updates lane state and error counters."""
        t = now if now is not None else time.time()
        self.active_requests = max(0, self.active_requests - 1)

        if success:
            self.error_count = 0
            if self.requests_used >= self.configured_test_request_limit:
                self.state = LaneState.DAILY_EXHAUSTED
            elif self.active_requests >= self.max_concurrent_requests:
                self.state = LaneState.BUSY
            else:
                self.state = LaneState.AVAILABLE
        else:
            self.error_count += 1
            self.last_error_time = t
            err_str = str(error).lower() if error else ""

            if status_code == 429 or "429" in err_str or "rate limit" in err_str:
                self.state = LaneState.RATE_LIMITED
                self.cooldown_until = t + cooldown_seconds
            else:
                if self.error_count >= 3:
                    self.state = LaneState.DEGRADED
                    self.cooldown_until = t + cooldown_seconds
                elif self.requests_used >= self.configured_test_request_limit:
                    self.state = LaneState.DAILY_EXHAUSTED
                else:
                    self.state = LaneState.AVAILABLE
