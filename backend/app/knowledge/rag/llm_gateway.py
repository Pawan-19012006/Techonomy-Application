"""LLMGateway handling model selection, HTTP connection reuse, retries with backoff, model fallback, reasoning isolation at API level, and token streaming."""

import asyncio
import json
import re
import time
from typing import Any, AsyncGenerator, Dict, Optional, Tuple
import httpx

from app.config import settings
from app.knowledge.exceptions import (
    LLMServiceError,
    LLMTimeoutError,
    OpenRouterAPIError,
)
from app.utils.logging import logger

_shared_async_client: Optional[httpx.AsyncClient] = None
_shared_sync_client: Optional[httpx.Client] = None


def get_shared_async_client() -> httpx.AsyncClient:
    """Returns or creates shared httpx.AsyncClient with connection pooling."""
    global _shared_async_client
    if _shared_async_client is None or _shared_async_client.is_closed:
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
        _shared_async_client = httpx.AsyncClient(
            limits=limits,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
    return _shared_async_client


def get_shared_sync_client() -> httpx.Client:
    """Returns or creates shared httpx.Client for synchronous calls."""
    global _shared_sync_client
    if _shared_sync_client is None or _shared_sync_client.is_closed:
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
        _shared_sync_client = httpx.Client(
            limits=limits,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
    return _shared_sync_client


async def close_shared_clients() -> None:
    """Closes shared HTTP client pools on application shutdown."""
    global _shared_async_client, _shared_sync_client
    if _shared_async_client is not None and not _shared_async_client.is_closed:
        await _shared_async_client.aclose()
        _shared_async_client = None
    if _shared_sync_client is not None and not _shared_sync_client.is_closed:
        _shared_sync_client.close()
        _shared_sync_client = None


def extract_clean_answer(data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Extracts clean final text content from OpenRouter response payload, discarding reasoning and recording execution metrics."""
    if "choices" not in data or not data["choices"]:
        raise OpenRouterAPIError("OpenRouter API returned empty choices list.")

    choice = data["choices"][0]
    message = choice.get("message", {})
    finish_reason = choice.get("finish_reason", "unknown")

    # Extract strictly message.content as the final answer
    content = message.get("content", "") or ""

    # Optional fallback clean up if model includes XML think tags inside content
    if "<think>" in content:
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()

    clean_content = content.strip()

    if not clean_content:
        raise OpenRouterAPIError("OpenRouter API returned empty text response.")

    usage = data.get("usage", {})
    details = usage.get("completion_tokens_details", {}) or {}
    reasoning_tokens = details.get("reasoning_tokens", usage.get("reasoning_tokens", 0))

    metrics = {
        "finish_reason": finish_reason,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "reasoning_tokens": reasoning_tokens,
        "total_tokens": usage.get("total_tokens"),
    }

    return clean_content, metrics


class LLMGateway:
    """Production LLM Gateway managing OpenRouter request execution, retries, exponential backoff, model fallback, API-level reasoning suppression, and streaming."""

    def __init__(
        self,
        api_key: str = settings.OPENROUTER_API_KEY,
        primary_model: str = settings.PRIMARY_MODEL,
        fallback_model: Optional[str] = settings.FALLBACK_MODEL,
        base_url: str = settings.OPENROUTER_BASE_URL,
        timeout_seconds: float = settings.LLM_TIMEOUT_SECONDS,
        max_retries: int = settings.LLM_MAX_RETRIES,
        max_tokens: int = settings.LLM_MAX_TOKENS,
    ):
        """Initializes LLMGateway parameters."""
        self.api_key = api_key
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_tokens = max_tokens

    def _build_payload(self, prompt: str, model_name: str, stream: bool = False) -> Dict[str, Any]:
        """Constructs JSON request payload for OpenRouter chat completions with reasoning suppressed at API level."""
        return {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.1,
            "max_tokens": self.max_tokens,
            "stream": stream,
            "reasoning": {"max_tokens": 0},
        }

    def _build_headers(self) -> Dict[str, str]:
        """Constructs HTTP headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://techonomy.ai",
            "X-Title": "Techonomy Enterprise Knowledge Platform",
            "Content-Type": "application/json",
        }

    async def _execute_attempt_async(
        self, client: httpx.AsyncClient, url: str, headers: Dict[str, str], payload: Dict[str, Any], model_name: str
    ) -> str:
        """Executes a single async LLM generation HTTP attempt with retries and exponential backoff."""
        for attempt in range(self.max_retries + 1):
            attempt_num = attempt + 1
            t_start = time.perf_counter()

            try:
                response = await client.post(url, headers=headers, json=payload, timeout=self.timeout_seconds)
                duration = time.perf_counter() - t_start
                status_code = response.status_code
                response.raise_for_status()
                data = response.json()

                clean_answer, metrics = extract_clean_answer(data)

                finish_reason = metrics.get("finish_reason", "unknown")
                prompt_tokens = metrics.get("prompt_tokens")
                completion_tokens = metrics.get("completion_tokens")
                reasoning_tokens = metrics.get("reasoning_tokens")
                total_tokens = metrics.get("total_tokens")

                logger.info(
                    f"\n[LLM GENERATION METRICS]\n"
                    f"provider=OpenRouter\n"
                    f"model={model_name}\n"
                    f"attempt={attempt_num}\n"
                    f"duration={duration:.3f}s\n"
                    f"status={status_code}\n"
                    f"finish_reason={finish_reason}\n"
                    f"prompt_tokens={prompt_tokens}\n"
                    f"completion_tokens={completion_tokens}\n"
                    f"reasoning_tokens={reasoning_tokens}\n"
                    f"total_tokens={total_tokens}\n"
                    f"success=True"
                )

                if finish_reason == "length":
                    logger.warning(
                        f"[LLM WARNING] Answer generation reached max_tokens limit ({self.max_tokens}) "
                        f"for model '{model_name}' (finish_reason='length')!"
                    )

                return clean_answer

            except (httpx.TimeoutException, httpx.HTTPStatusError, Exception) as exc:
                duration = time.perf_counter() - t_start
                is_timeout = isinstance(exc, httpx.TimeoutException)
                status_code = getattr(getattr(exc, "response", None), "status_code", "timeout" if is_timeout else "error")

                logger.warning(
                    f"\n[LLM ATTEMPT FAILED]\n"
                    f"model={model_name}\n"
                    f"attempt={attempt_num}\n"
                    f"duration={duration:.3f}s\n"
                    f"status={status_code}\n"
                    f"error={exc}"
                )

                if attempt < self.max_retries:
                    backoff = 0.5 * (2 ** attempt)
                    await asyncio.sleep(backoff)
                    continue

                if is_timeout:
                    raise LLMTimeoutError(f"OpenRouter API request timed out after {self.timeout_seconds}s.") from exc
                raise exc

    async def generate_async(self, prompt: str) -> str:
        """Generates LLM completion asynchronously using primary model and fallback model resilience."""
        if not prompt or not prompt.strip():
            raise LLMServiceError("Prompt cannot be empty.")

        if not self.api_key:
            raise OpenRouterAPIError("API key is missing. OPENROUTER_API_KEY environment variable must be configured.")

        url = f"{self.base_url}/chat/completions"
        headers = self._build_headers()
        client = get_shared_async_client()

        try:
            payload = self._build_payload(prompt, self.primary_model)
            return await self._execute_attempt_async(client, url, headers, payload, self.primary_model)
        except Exception as primary_exc:
            if not self.fallback_model or self.fallback_model == self.primary_model:
                raise primary_exc

            logger.warning(f"[LLM GATEWAY FALLBACK] Primary model '{self.primary_model}' failed ({primary_exc}). Trying fallback '{self.fallback_model}'...")
            try:
                fallback_payload = self._build_payload(prompt, self.fallback_model)
                return await self._execute_attempt_async(client, url, headers, fallback_payload, self.fallback_model)
            except Exception as fallback_exc:
                logger.error(f"[LLM GATEWAY CRITICAL] Both primary and fallback models failed: {fallback_exc}")
                if isinstance(fallback_exc, (LLMTimeoutError, OpenRouterAPIError)):
                    raise fallback_exc
                raise OpenRouterAPIError(f"LLM generation failed across primary and fallback models: {primary_exc}") from fallback_exc

    async def generate_stream_async(self, prompt: str) -> AsyncGenerator[str, None]:
        """Yields text tokens progressively as SSE chunks while strictly filtering reasoning tokens."""
        if not prompt or not prompt.strip():
            yield "Prompt cannot be empty."
            return

        if not self.api_key:
            yield "OPENROUTER_API_KEY is missing."
            return

        url = f"{self.base_url}/chat/completions"
        headers = self._build_headers()
        client = get_shared_async_client()
        payload = self._build_payload(prompt, self.primary_model, stream=True)

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

                            # Discard separate reasoning / thinking fields
                            if "reasoning" in delta or "thinking" in delta or "reasoning_details" in delta:
                                continue

                            content_chunk = delta.get("content")
                            if content_chunk:
                                yield content_chunk
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f"Streaming token generation failed: {e}")
            yield f"\n[Streaming error: {str(e)}]"

    def generate(self, prompt: str) -> str:
        """Generates LLM completion synchronously using primary and fallback models."""
        if not prompt or not prompt.strip():
            raise LLMServiceError("Prompt cannot be empty.")

        if not self.api_key:
            raise OpenRouterAPIError("API key is missing. OPENROUTER_API_KEY environment variable must be configured.")

        url = f"{self.base_url}/chat/completions"
        headers = self._build_headers()
        client = get_shared_sync_client()

        models_to_try = [self.primary_model]
        if self.fallback_model and self.fallback_model != self.primary_model:
            models_to_try.append(self.fallback_model)

        last_timeout_exc = None

        for model_name in models_to_try:
            payload = self._build_payload(prompt, model_name)
            for attempt in range(self.max_retries + 1):
                attempt_num = attempt + 1
                t_start = time.perf_counter()
                try:
                    response = client.post(url, headers=headers, json=payload, timeout=self.timeout_seconds)
                    duration = time.perf_counter() - t_start
                    status_code = response.status_code
                    response.raise_for_status()
                    data = response.json()

                    clean_answer, metrics = extract_clean_answer(data)

                    finish_reason = metrics.get("finish_reason", "unknown")
                    prompt_tokens = metrics.get("prompt_tokens")
                    completion_tokens = metrics.get("completion_tokens")
                    reasoning_tokens = metrics.get("reasoning_tokens")
                    total_tokens = metrics.get("total_tokens")

                    logger.info(
                        f"\n[LLM GENERATION METRICS]\n"
                        f"provider=OpenRouter\n"
                        f"model={model_name}\n"
                        f"attempt={attempt_num}\n"
                        f"duration={duration:.3f}s\n"
                        f"status={status_code}\n"
                        f"finish_reason={finish_reason}\n"
                        f"prompt_tokens={prompt_tokens}\n"
                        f"completion_tokens={completion_tokens}\n"
                        f"reasoning_tokens={reasoning_tokens}\n"
                        f"total_tokens={total_tokens}\n"
                        f"success=True"
                    )

                    if finish_reason == "length":
                        logger.warning(
                            f"[LLM WARNING] Answer generation reached max_tokens limit ({self.max_tokens}) "
                            f"for model '{model_name}' (finish_reason='length')!"
                        )

                    return clean_answer
                except httpx.TimeoutException as exc:
                    duration = time.perf_counter() - t_start
                    logger.warning(f"Sync attempt {attempt_num} timed out for model '{model_name}' in {duration:.3f}s: {exc}")
                    last_timeout_exc = LLMTimeoutError(f"OpenRouter API request timed out after {self.timeout_seconds}s.")
                    if attempt < self.max_retries:
                        time.sleep(0.5)
                        continue
                except Exception as exc:
                    duration = time.perf_counter() - t_start
                    logger.warning(f"Sync attempt {attempt_num} failed for model '{model_name}' in {duration:.3f}s: {exc}")
                    if attempt < self.max_retries:
                        time.sleep(0.5)
                        continue

        if last_timeout_exc is not None:
            raise last_timeout_exc
        raise OpenRouterAPIError("LLM generation failed synchronously across configured models.")
