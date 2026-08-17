"""LLMGateway handling quota-aware model scheduling, connection reuse, reasoning isolation, and token streaming."""

import asyncio
import json
import re
import time
from typing import Any, AsyncGenerator, Dict, Optional, Tuple

from app.config import settings
from app.knowledge.exceptions import (
    LLMQuotaExhaustedError,
    LLMServiceError,
    LLMTimeoutError,
    OpenRouterAPIError,
)
from app.knowledge.rag.providers import (
    GeminiProviderAdapter,
    LLMProvider,
    NemotronProviderAdapter,
    close_shared_clients,
    extract_clean_answer,
    get_shared_async_client,
    get_shared_sync_client,
)
from app.knowledge.rag.scheduler import QuotaScheduler
from app.utils.logging import logger
from app.utils.observability import (
    get_request_id,
    log_structured_event,
    sanitize_error_message,
)


class LLMGateway:
    """Production LLM Gateway integrating QuotaScheduler and Provider Adapters."""

    def __init__(
        self,
        api_key: str = settings.OPENROUTER_API_KEY,
        primary_model: str = settings.PRIMARY_MODEL,
        fallback_model: Optional[str] = settings.FALLBACK_MODEL,
        base_url: str = settings.OPENROUTER_BASE_URL,
        timeout_seconds: float = settings.LLM_TIMEOUT_SECONDS,
        max_retries: int = settings.LLM_MAX_RETRIES,
        max_tokens: int = settings.LLM_MAX_TOKENS,
        scheduler: Optional[QuotaScheduler] = None,
        gemini_adapter: Optional[LLMProvider] = None,
        nemotron_adapter: Optional[LLMProvider] = None,
    ):
        """Initializes LLMGateway and injected or default QuotaScheduler & Provider Adapters."""
        self.api_key = api_key
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_tokens = max_tokens

        self.scheduler = scheduler or QuotaScheduler(
            gemini_api_key=settings.GEMINI_API_KEY,
            nemotron_api_key=api_key,
            gemini_enabled=settings.GEMINI_ENABLED,
            nemotron_enabled=settings.NEMOTRON_ENABLED,
            gemini_model=settings.GEMINI_MODEL,
            nemotron_model=primary_model,
            gemini_test_limit=settings.GEMINI_TEST_REQUEST_LIMIT,
            nemotron_test_limit=settings.NEMOTRON_TEST_REQUEST_LIMIT,
            gemini_max_concurrency=settings.GEMINI_MAX_CONCURRENT_REQUESTS,
            nemotron_max_concurrency=settings.NEMOTRON_MAX_CONCURRENT_REQUESTS,
            gemini_num_lanes=settings.GEMINI_NUM_LANES,
            nemotron_num_lanes=settings.NEMOTRON_NUM_LANES,
            cooldown_seconds=settings.SCHEDULER_COOLDOWN_SECONDS,
        )

        self.gemini_adapter = gemini_adapter or GeminiProviderAdapter()
        self.nemotron_adapter = nemotron_adapter or NemotronProviderAdapter(base_url=self.base_url)

    def _get_adapter(self, provider: str) -> LLMProvider:
        """Resolves provider adapter instance based on provider name."""
        if provider == "gemini":
            return self.gemini_adapter
        return self.nemotron_adapter

    async def generate_async(
        self,
        prompt: str,
        request_id: Optional[str] = None,
        tracker: Optional[Any] = None,
    ) -> str:
        """Generates LLM completion asynchronously via QuotaScheduler and Provider Adapters."""
        if not prompt or not prompt.strip():
            raise LLMServiceError("Prompt cannot be empty.")

        req_id = get_request_id(request_id)
        lane, key_val, is_fallback = await self.scheduler.select_lane_async()
        
        logger.info(
            f"[LLM_ROUTE] provider={lane.provider} lane={lane.lane_id} fallback={is_fallback} "
            f"active={lane.active_requests} remaining={lane.requests_remaining}"
        )
        log_structured_event(
            "LLM_GEN_START",
            req_id,
            provider=lane.provider,
            lane=lane.lane_id,
            fallback=is_fallback,
            model=lane.model,
            max_tokens=self.max_tokens,
        )

        adapter = self._get_adapter(lane.provider)
        t_start = time.perf_counter()

        try:
            result = await adapter.generate_async(
                prompt=prompt,
                model=lane.model,
                api_key=key_val,
                timeout_seconds=self.timeout_seconds,
                max_retries=self.max_retries,
                max_tokens=self.max_tokens,
            )
            duration_ms = (time.perf_counter() - t_start) * 1000.0
            self.scheduler.release_lane(lane.lane_id, success=True)

            log_structured_event(
                "LLM_STREAM_COMPLETE",
                req_id,
                duration_ms=round(duration_ms, 2),
                provider=lane.provider,
                model=lane.model,
                fallback=is_fallback,
                chunks=1,
                finish_reason="STOP",
            )
            if tracker and hasattr(tracker, "record_llm_complete"):
                try:
                    tracker.record_llm_complete(
                        total_duration_ms=duration_ms,
                        provider=lane.provider,
                        model=lane.model,
                        fallback=is_fallback,
                        chunk_count=1,
                        finish_reason="STOP",
                    )
                except Exception as t_err:
                    logger.warning(f"Tracker record failed in generate_async: {t_err}")

            return result
        except Exception as exc:
            duration_ms = (time.perf_counter() - t_start) * 1000.0
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            self.scheduler.release_lane(lane.lane_id, success=False, status_code=status_code, error=exc)
            
            log_structured_event(
                "STAGE_FAILURE",
                req_id,
                stage="llm",
                provider=lane.provider,
                duration_ms=round(duration_ms, 2),
                error_type=type(exc).__name__,
            )
            raise exc

    def generate(
        self,
        prompt: str,
        request_id: Optional[str] = None,
        tracker: Optional[Any] = None,
    ) -> str:
        """Generates LLM completion synchronously via QuotaScheduler and Provider Adapters."""
        if not prompt or not prompt.strip():
            raise LLMServiceError("Prompt cannot be empty.")

        req_id = get_request_id(request_id)
        lane, key_val, is_fallback = self.scheduler.select_lane_sync()

        log_structured_event(
            "LLM_GEN_START",
            req_id,
            provider=lane.provider,
            lane=lane.lane_id,
            fallback=is_fallback,
            model=lane.model,
            max_tokens=self.max_tokens,
        )

        adapter = self._get_adapter(lane.provider)
        t_start = time.perf_counter()

        try:
            result = adapter.generate(
                prompt=prompt,
                model=lane.model,
                api_key=key_val,
                timeout_seconds=self.timeout_seconds,
                max_retries=self.max_retries,
                max_tokens=self.max_tokens,
            )
            duration_ms = (time.perf_counter() - t_start) * 1000.0
            self.scheduler.release_lane(lane.lane_id, success=True)

            log_structured_event(
                "LLM_STREAM_COMPLETE",
                req_id,
                duration_ms=round(duration_ms, 2),
                provider=lane.provider,
                model=lane.model,
                fallback=is_fallback,
                chunks=1,
                finish_reason="STOP",
            )
            if tracker and hasattr(tracker, "record_llm_complete"):
                try:
                    tracker.record_llm_complete(
                        total_duration_ms=duration_ms,
                        provider=lane.provider,
                        model=lane.model,
                        fallback=is_fallback,
                        chunk_count=1,
                        finish_reason="STOP",
                    )
                except Exception as t_err:
                    logger.warning(f"Tracker record failed in generate: {t_err}")

            return result
        except Exception as exc:
            duration_ms = (time.perf_counter() - t_start) * 1000.0
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            self.scheduler.release_lane(lane.lane_id, success=False, status_code=status_code, error=exc)

            log_structured_event(
                "STAGE_FAILURE",
                req_id,
                stage="llm",
                provider=lane.provider,
                duration_ms=round(duration_ms, 2),
                error_type=type(exc).__name__,
            )
            raise exc

    async def generate_stream_async(
        self,
        prompt: str,
        request_id: Optional[str] = None,
        tracker: Optional[Any] = None,
    ) -> AsyncGenerator[str, None]:
        """Yields text tokens progressively while retaining lane reservation for the entire stream lifetime."""
        if not prompt or not prompt.strip():
            yield "Prompt cannot be empty."
            return

        req_id = get_request_id(request_id)
        lane, key_val, is_fallback = await self.scheduler.select_lane_async()

        log_structured_event(
            "LLM_GEN_START",
            req_id,
            provider=lane.provider,
            lane=lane.lane_id,
            fallback=is_fallback,
            model=lane.model,
            max_tokens=self.max_tokens,
        )

        adapter = self._get_adapter(lane.provider)
        t_start = time.perf_counter()
        t_first_token: Optional[float] = None
        ttft_ms: Optional[float] = None

        stream_success = False
        last_error = None
        chunk_count = 0
        char_count = 0
        last_finish_reason = None

        try:
            async for chunk, finish_reason in adapter.generate_stream_async(
                prompt=prompt,
                model=lane.model,
                api_key=key_val,
                timeout_seconds=self.timeout_seconds,
                max_tokens=self.max_tokens,
            ):
                if finish_reason:
                    last_finish_reason = finish_reason

                if chunk:
                    if t_first_token is None:
                        t_first_token = time.perf_counter()
                        ttft_ms = (t_first_token - t_start) * 1000.0
                        log_structured_event("LLM_FIRST_TOKEN", req_id, ttft_ms=round(ttft_ms, 2))
                        if tracker and hasattr(tracker, "record_llm_first_token"):
                            try:
                                tracker.record_llm_first_token(ttft_ms)
                            except Exception as t_err:
                                logger.warning(f"Tracker record_llm_first_token failed: {t_err}")

                    chunk_count += 1
                    char_count += len(chunk)
                    yield chunk

            if last_finish_reason in ("MAX_TOKENS", "length"):
                notice = f"\n\n*(Note: Output reached configured token limit of {self.max_tokens}. Ask a follow-up question for remaining details.)*"
                char_count += len(notice)
                yield notice

            stream_success = True
        except Exception as e:
            last_error = e
            logger.error(f"Streaming token generation failed for lane '{lane.lane_id}': {sanitize_error_message(e)}")
            yield f"\n[Streaming error: {sanitize_error_message(e)}]"
        finally:
            t_end = time.perf_counter()
            total_duration_ms = (t_end - t_start) * 1000.0
            stream_duration_ms = ((t_end - t_first_token) * 1000.0) if t_first_token else total_duration_ms

            status_code = getattr(getattr(last_error, "response", None), "status_code", None)
            self.scheduler.release_lane(
                lane.lane_id,
                success=stream_success,
                status_code=status_code,
                error=last_error,
            )

            if stream_success:
                log_structured_event(
                    "LLM_STREAM_COMPLETE",
                    req_id,
                    duration_ms=round(total_duration_ms, 2),
                    provider=lane.provider,
                    model=lane.model,
                    fallback=is_fallback,
                    chunks=chunk_count,
                    finish_reason=last_finish_reason or "STOP",
                    ttft_ms=round(ttft_ms, 2) if ttft_ms else None,
                    stream_duration_ms=round(stream_duration_ms, 2),
                )
                if tracker and hasattr(tracker, "record_llm_complete"):
                    try:
                        tracker.record_llm_complete(
                            total_duration_ms=total_duration_ms,
                            provider=lane.provider,
                            model=lane.model,
                            fallback=is_fallback,
                            chunk_count=chunk_count,
                            finish_reason=last_finish_reason or "STOP",
                            stream_duration_ms=stream_duration_ms,
                        )
                    except Exception as t_err:
                        logger.warning(f"Tracker record_llm_complete failed: {t_err}")
            else:
                log_structured_event(
                    "STAGE_FAILURE",
                    req_id,
                    stage="llm",
                    provider=lane.provider,
                    duration_ms=round(total_duration_ms, 2),
                    error_type=type(last_error).__name__ if last_error else "UnknownError",
                )
