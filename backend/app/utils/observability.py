"""Production Latency Observability Module for Techonomy RAG Pipeline.

Provides request correlation ID propagation, high-resolution stage timers using time.perf_counter(),
structured log formatting, error credential sanitization, and non-blocking latency breakdown summaries.
"""

from contextvars import ContextVar
from datetime import datetime, timezone
import time
import uuid
from typing import Any, Dict, Optional, Union

from app.config import settings
from app.utils.logging import logger

# ContextVar for propagating request_id across async/thread boundaries
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def generate_request_id() -> str:
    """Generates a unique, non-sensitive server-side request ID."""
    return f"req_{uuid.uuid4().hex[:12]}"


def get_request_id(explicit_id: Optional[str] = None) -> str:
    """Retrieves current request ID from explicit argument, ContextVar, or fallback default."""
    if explicit_id and explicit_id.strip():
        return explicit_id.strip()
    ctx_id = request_id_var.get()
    if ctx_id and ctx_id.strip():
        return ctx_id.strip()
    return "req_system"


def set_request_id(request_id: str) -> None:
    """Sets current request ID in context variable."""
    if request_id:
        request_id_var.set(request_id.strip())


def sanitize_error_message(err: Union[str, Exception]) -> str:
    """Sanitizes exception or string message to prevent credential leaks in logs."""
    msg = str(err)
    if not msg:
        return "UnknownError"

    # Redact sensitive API keys if present
    for secret in (settings.GEMINI_API_KEY, settings.OPENROUTER_API_KEY, settings.QDRANT_API_KEY):
        if secret and len(secret.strip()) > 4 and secret in msg:
            msg = msg.replace(secret, "[REDACTED_API_KEY]")

    return msg


def log_structured_event(
    event_name: str,
    request_id: Optional[str] = None,
    duration_ms: Optional[float] = None,
    **kwargs: Any,
) -> None:
    """Emits structured, machine-readable key-value log entry with timestamp and request_id.
    
    Guaranteed not to raise exceptions even if formatting fails.
    """
    try:
        req_id = get_request_id(request_id)
        iso_timestamp = datetime.now(timezone.utc).isoformat()
        kv_pairs = [f"request_id={req_id}", f"timestamp={iso_timestamp}"]

        if duration_ms is not None:
            kv_pairs.append(f"duration_ms={duration_ms:.2f}")

        for k, v in kwargs.items():
            if v is not None:
                # Sanitize string values for safety
                val_str = str(v)
                for secret in (settings.GEMINI_API_KEY, settings.OPENROUTER_API_KEY, settings.QDRANT_API_KEY):
                    if secret and len(secret.strip()) > 4 and secret in val_str:
                        val_str = val_str.replace(secret, "[REDACTED_API_KEY]")
                kv_pairs.append(f"{k}={val_str}")

        formatted_kv = " ".join(kv_pairs)
        logger.info(f"[{event_name}] {formatted_kv}")
    except Exception as e:
        logger.warning(f"[LOGGING_ERROR] Failed to emit structured log event '{event_name}': {e}")


class LatencyTracker:
    """Lightweight timing collector tracking stage latencies for a RAG request."""

    def __init__(self, request_id: Optional[str] = None):
        self.request_id = get_request_id(request_id)
        self.req_start_time = time.perf_counter()

        # Measured durations in ms
        self.db_team_lookup_ms: Optional[float] = None
        self.db_quota_reservation_ms: Optional[float] = None
        self.embedding_ms: Optional[float] = None
        self.qdrant_ms: Optional[float] = None
        self.qdrant_chunks_retrieved: int = 0
        self.qdrant_succeeded: bool = True
        self.qdrant_zero_results: bool = False
        self.rerank_ms: Optional[float] = None
        self.context_build_ms: Optional[float] = None
        self.llm_ttft_ms: Optional[float] = None
        self.llm_stream_duration_ms: Optional[float] = None
        self.llm_total_duration_ms: Optional[float] = None
        self.llm_provider: Optional[str] = None
        self.llm_model: Optional[str] = None
        self.llm_fallback: bool = False
        self.llm_chunks: int = 0
        self.llm_finish_reason: Optional[str] = None
        self.rag_pipeline_duration_ms: Optional[float] = None

    def record_db_team_lookup(self, duration_ms: float) -> None:
        """Records DB team lookup duration."""
        self.db_team_lookup_ms = round(duration_ms, 2)
        log_structured_event("DB_TEAM_LOOKUP_COMPLETE", self.request_id, duration_ms=self.db_team_lookup_ms)

    def record_db_quota_reservation(self, duration_ms: float, reserved: bool) -> None:
        """Records DB prompt quota reservation duration."""
        self.db_quota_reservation_ms = round(duration_ms, 2)
        log_structured_event(
            "DB_QUOTA_RESERVATION_COMPLETE",
            self.request_id,
            duration_ms=self.db_quota_reservation_ms,
            reserved=reserved,
        )

    def record_embedding(self, duration_ms: float) -> None:
        """Records query embedding generator duration."""
        self.embedding_ms = round(duration_ms, 2)
        log_structured_event("EMBEDDING_COMPLETE", self.request_id, duration_ms=self.embedding_ms)

    def record_qdrant(
        self,
        duration_ms: float,
        chunk_count: int,
        succeeded: bool = True,
        zero_results: bool = False,
    ) -> None:
        """Records Qdrant vector retrieval metrics."""
        self.qdrant_ms = round(duration_ms, 2)
        self.qdrant_chunks_retrieved = chunk_count
        self.qdrant_succeeded = succeeded
        self.qdrant_zero_results = zero_results
        log_structured_event(
            "QDRANT_RETRIEVAL_COMPLETE",
            self.request_id,
            duration_ms=self.qdrant_ms,
            chunks=chunk_count,
            succeeded=succeeded,
            zero_results=zero_results,
        )

    def record_llm_first_token(self, ttft_ms: float) -> None:
        """Records time-to-first-token (TTFT) for streaming LLM generation."""
        self.llm_ttft_ms = round(ttft_ms, 2)
        log_structured_event("LLM_FIRST_TOKEN", self.request_id, ttft_ms=self.llm_ttft_ms)

    def record_llm_complete(
        self,
        total_duration_ms: float,
        provider: str,
        model: str,
        fallback: bool,
        chunk_count: int,
        finish_reason: Optional[str] = None,
        stream_duration_ms: Optional[float] = None,
    ) -> None:
        """Records complete LLM generation stage metrics."""
        self.llm_total_duration_ms = round(total_duration_ms, 2)
        self.llm_provider = provider
        self.llm_model = model
        self.llm_fallback = fallback
        self.llm_chunks = chunk_count
        self.llm_finish_reason = finish_reason
        if stream_duration_ms is not None:
            self.llm_stream_duration_ms = round(stream_duration_ms, 2)

        log_structured_event(
            "LLM_GENERATION_COMPLETE",
            self.request_id,
            duration_ms=self.llm_total_duration_ms,
            provider=provider,
            model=model,
            fallback=fallback,
            chunks=chunk_count,
            finish_reason=finish_reason or "unknown",
            ttft_ms=self.llm_ttft_ms,
            stream_duration_ms=self.llm_stream_duration_ms,
        )

    def emit_summary(self, rag_total_ms: Optional[float] = None) -> None:
        """Emits concise, structured latency breakdown summary."""
        try:
            if rag_total_ms is None:
                rag_total_ms = (time.perf_counter() - self.req_start_time) * 1000.0
            self.rag_pipeline_duration_ms = round(rag_total_ms, 2)

            db_total_ms = (self.db_team_lookup_ms or 0.0) + (self.db_quota_reservation_ms or 0.0)

            log_structured_event(
                "RAG_LATENCY_SUMMARY",
                self.request_id,
                total_ms=self.rag_pipeline_duration_ms,
                embedding_ms=self.embedding_ms or 0.0,
                qdrant_ms=self.qdrant_ms or 0.0,
                database_ms=round(db_total_ms, 2),
                llm_ttft_ms=self.llm_ttft_ms or 0.0,
                llm_generation_ms=self.llm_total_duration_ms or 0.0,
            )
        except Exception as e:
            logger.warning(f"[LOGGING_ERROR] Failed to emit latency summary for request '{self.request_id}': {e}")
