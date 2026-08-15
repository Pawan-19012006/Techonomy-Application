"""LLMGateway handling quota-aware model scheduling, connection reuse, reasoning isolation, and token streaming."""

import asyncio
import json
import re
import time
from typing import Any, AsyncGenerator, Dict, Optional, Tuple
import httpx

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

    async def generate_async(self, prompt: str) -> str:
        """Generates LLM completion asynchronously via QuotaScheduler and Provider Adapters."""
        if not prompt or not prompt.strip():
            raise LLMServiceError("Prompt cannot be empty.")

        lane, key_val, is_fallback = await self.scheduler.select_lane_async()
        logger.info(
            f"[LLM_ROUTE] provider={lane.provider} lane={lane.lane_id} fallback={is_fallback} "
            f"active={lane.active_requests} remaining={lane.requests_remaining}"
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
            duration = time.perf_counter() - t_start
            self.scheduler.release_lane(lane.lane_id, success=True)
            logger.info(f"[LLM_COMPLETE] provider={lane.provider} lane={lane.lane_id} duration={duration:.3f}s success=True")
            return result
        except Exception as exc:
            duration = time.perf_counter() - t_start
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            self.scheduler.release_lane(lane.lane_id, success=False, status_code=status_code, error=exc)
            logger.warning(f"[LLM_FAILURE] provider={lane.provider} lane={lane.lane_id} duration={duration:.3f}s error={exc}")
            raise exc

    def generate(self, prompt: str) -> str:
        """Generates LLM completion synchronously via QuotaScheduler and Provider Adapters."""
        if not prompt or not prompt.strip():
            raise LLMServiceError("Prompt cannot be empty.")

        lane, key_val, is_fallback = self.scheduler.select_lane_sync()
        logger.info(
            f"[LLM_ROUTE] provider={lane.provider} lane={lane.lane_id} fallback={is_fallback} "
            f"active={lane.active_requests} remaining={lane.requests_remaining}"
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
            duration = time.perf_counter() - t_start
            self.scheduler.release_lane(lane.lane_id, success=True)
            logger.info(f"[LLM_COMPLETE] provider={lane.provider} lane={lane.lane_id} duration={duration:.3f}s success=True")
            return result
        except Exception as exc:
            duration = time.perf_counter() - t_start
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            self.scheduler.release_lane(lane.lane_id, success=False, status_code=status_code, error=exc)
            logger.warning(f"[LLM_FAILURE] provider={lane.provider} lane={lane.lane_id} duration={duration:.3f}s error={exc}")
            raise exc

    async def generate_stream_async(self, prompt: str) -> AsyncGenerator[str, None]:
        """Yields text tokens progressively while retaining lane reservation for the entire stream lifetime."""
        if not prompt or not prompt.strip():
            yield "Prompt cannot be empty."
            return

        lane, key_val, is_fallback = await self.scheduler.select_lane_async()
        logger.info(
            f"[LLM_ROUTE_STREAM] provider={lane.provider} lane={lane.lane_id} fallback={is_fallback} "
            f"active={lane.active_requests} remaining={lane.requests_remaining}"
        )

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {key_val}",
            "HTTP-Referer": "https://techonomy.ai",
            "X-Title": "Techonomy Enterprise Knowledge Platform",
            "Content-Type": "application/json",
        }
        payload = {
            "model": lane.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": self.max_tokens,
            "stream": True,
            "reasoning": {"max_tokens": 0},
        }

        client = get_shared_async_client()
        stream_success = False
        last_error = None

        try:
            async with client.stream("POST", url, headers=headers, json=payload, timeout=self.timeout_seconds) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data_json = json.loads(data_str)
                            delta = data_json["choices"][0]["delta"]

                            if "reasoning" in delta or "thinking" in delta or "reasoning_details" in delta:
                                continue

                            content_chunk = delta.get("content")
                            if content_chunk:
                                yield content_chunk
                        except Exception:
                            continue
            stream_success = True
        except Exception as e:
            last_error = e
            logger.error(f"Streaming token generation failed for lane '{lane.lane_id}': {e}")
            yield f"\n[Streaming error: {str(e)}]"
        finally:
            # Crucial requirement: Lane slot is released ONLY after stream completion, failure, or cancellation
            status_code = getattr(getattr(last_error, "response", None), "status_code", None)
            self.scheduler.release_lane(
                lane.lane_id,
                success=stream_success,
                status_code=status_code,
                error=last_error,
            )
            logger.info(f"[LLM_STREAM_COMPLETE] provider={lane.provider} lane={lane.lane_id} success={stream_success}")
