"""LLMService handling OpenRouter API generation calls with timeouts, retry resilience, and timing instrumentation."""

import asyncio
import time
from typing import Any, Dict, Optional
import httpx

from app.config import settings
from app.knowledge.exceptions import (
    LLMServiceError,
    LLMTimeoutError,
    OpenRouterAPIError,
)
from app.utils.logging import logger


class LLMService:
    """Service wrapping OpenRouter API calls for text completion with high-resolution timing, timeout, and retry visibility."""

    def __init__(
        self,
        api_key: str = settings.OPENROUTER_API_KEY,
        model: str = settings.OPENROUTER_MODEL,
        base_url: str = settings.OPENROUTER_BASE_URL,
        timeout_seconds: float = settings.LLM_TIMEOUT_SECONDS,
        max_retries: int = settings.LLM_MAX_RETRIES,
        max_tokens: int = 500,
    ):
        """Initializes LLMService with OpenRouter settings."""
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_tokens = max_tokens

    def _build_payload(self, prompt: str) -> Dict[str, Any]:
        """Constructs OpenRouter chat completion JSON request payload."""
        return {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.1,
            "max_tokens": self.max_tokens,
            "stream": False,
        }

    def _build_headers(self) -> Dict[str, str]:
        """Constructs HTTP request headers for OpenRouter API."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://techonomy.ai",
            "X-Title": "Techonomy Enterprise Knowledge Platform",
            "Content-Type": "application/json",
        }

    def _log_config(self) -> None:
        """Logs OpenRouter configuration details excluding API key."""
        logger.info(
            f"\n[LLM CONFIGURATION]\n"
            f"model={self.model}\n"
            f"temperature=0.1\n"
            f"max_tokens={self.max_tokens}\n"
            f"stream=False\n"
            f"reasoning=default/none\n"
            f"timeout={self.timeout_seconds}s\n"
            f"max_retries={self.max_retries}"
        )

    def generate(self, prompt: str, raise_on_missing_key: bool = False) -> str:
        """Executes synchronous OpenRouter API generation call with per-attempt high-resolution timing."""
        if not prompt or not prompt.strip():
            raise LLMServiceError("Prompt cannot be empty.")

        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY is not set in environment.")
            if raise_on_missing_key:
                raise OpenRouterAPIError(
                    "OpenRouter API key is missing. Configure OPENROUTER_API_KEY in environment."
                )
            return (
                "Retrieved company document context successfully. "
                "Configure OPENROUTER_API_KEY in environment for LLM text generation."
            )

        url = f"{self.base_url}/chat/completions"
        headers = self._build_headers()
        payload = self._build_payload(prompt)

        self._log_config()

        for attempt in range(self.max_retries + 1):
            attempt_num = attempt + 1
            t_attempt_start = time.perf_counter()

            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.post(url, headers=headers, json=payload)
                    duration = time.perf_counter() - t_attempt_start
                    status_code = response.status_code
                    response.raise_for_status()
                    data = response.json()

                    if "choices" not in data or not data["choices"]:
                        raise OpenRouterAPIError("OpenRouter API returned empty choices list.")

                    content = data["choices"][0]["message"]["content"]
                    if not content or not content.strip():
                        raise OpenRouterAPIError("OpenRouter API returned empty text response.")

                    logger.info(
                        f"\n[LLM ATTEMPT]\n"
                        f"attempt={attempt_num}\n"
                        f"model={self.model}\n"
                        f"duration={duration:.3f}s\n"
                        f"status={status_code}\n"
                        f"success=true"
                    )
                    return content.strip()

            except httpx.TimeoutException as te:
                duration = time.perf_counter() - t_attempt_start
                logger.warning(
                    f"\n[LLM ATTEMPT]\n"
                    f"attempt={attempt_num}\n"
                    f"model={self.model}\n"
                    f"duration={duration:.3f}s\n"
                    f"status=timeout\n"
                    f"success=false"
                )
                if attempt < self.max_retries:
                    time.sleep(1.0)
                    continue
                raise LLMTimeoutError(
                    f"OpenRouter API request timed out after {self.timeout_seconds} seconds."
                ) from te

            except httpx.HTTPStatusError as hse:
                duration = time.perf_counter() - t_attempt_start
                status_code = hse.response.status_code
                logger.warning(
                    f"\n[LLM ATTEMPT]\n"
                    f"attempt={attempt_num}\n"
                    f"model={self.model}\n"
                    f"duration={duration:.3f}s\n"
                    f"status={status_code}\n"
                    f"success=false"
                )
                if attempt < self.max_retries and status_code in (429, 500, 502, 503, 504):
                    time.sleep(1.0)
                    continue
                raise OpenRouterAPIError(f"OpenRouter HTTP {status_code}: {hse.response.text}") from hse

            except Exception as e:
                duration = time.perf_counter() - t_attempt_start
                logger.warning(
                    f"\n[LLM ATTEMPT]\n"
                    f"attempt={attempt_num}\n"
                    f"model={self.model}\n"
                    f"duration={duration:.3f}s\n"
                    f"status=error\n"
                    f"success=false"
                )
                if attempt < self.max_retries:
                    time.sleep(1.0)
                    continue
                raise OpenRouterAPIError(f"OpenRouter generation error: {str(e)}") from e

    async def generate_async(self, prompt: str, raise_on_missing_key: bool = False) -> str:
        """Executes asynchronous OpenRouter API generation call with per-attempt high-resolution timing."""
        if not prompt or not prompt.strip():
            raise LLMServiceError("Prompt cannot be empty.")

        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY is not set in environment.")
            if raise_on_missing_key:
                raise OpenRouterAPIError(
                    "OpenRouter API key is missing. Configure OPENROUTER_API_KEY in environment."
                )
            return (
                "Retrieved company document context successfully. "
                "Configure OPENROUTER_API_KEY in environment for LLM text generation."
            )

        url = f"{self.base_url}/chat/completions"
        headers = self._build_headers()
        payload = self._build_payload(prompt)

        self._log_config()

        for attempt in range(self.max_retries + 1):
            attempt_num = attempt + 1
            t_attempt_start = time.perf_counter()

            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    duration = time.perf_counter() - t_attempt_start
                    status_code = response.status_code
                    response.raise_for_status()
                    data = response.json()

                    if "choices" not in data or not data["choices"]:
                        raise OpenRouterAPIError("OpenRouter API returned empty choices list.")

                    content = data["choices"][0]["message"]["content"]
                    if not content or not content.strip():
                        raise OpenRouterAPIError("OpenRouter API returned empty text response.")

                    logger.info(
                        f"\n[LLM ATTEMPT]\n"
                        f"attempt={attempt_num}\n"
                        f"model={self.model}\n"
                        f"duration={duration:.3f}s\n"
                        f"status={status_code}\n"
                        f"success=true"
                    )
                    return content.strip()

            except httpx.TimeoutException as te:
                duration = time.perf_counter() - t_attempt_start
                logger.warning(
                    f"\n[LLM ATTEMPT]\n"
                    f"attempt={attempt_num}\n"
                    f"model={self.model}\n"
                    f"duration={duration:.3f}s\n"
                    f"status=timeout\n"
                    f"success=false"
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(1.0)
                    continue
                raise LLMTimeoutError(
                    f"OpenRouter API request timed out after {self.timeout_seconds} seconds."
                ) from te

            except httpx.HTTPStatusError as hse:
                duration = time.perf_counter() - t_attempt_start
                status_code = hse.response.status_code
                logger.warning(
                    f"\n[LLM ATTEMPT]\n"
                    f"attempt={attempt_num}\n"
                    f"model={self.model}\n"
                    f"duration={duration:.3f}s\n"
                    f"status={status_code}\n"
                    f"success=false"
                )
                if attempt < self.max_retries and status_code in (429, 500, 502, 503, 504):
                    await asyncio.sleep(1.0)
                    continue
                raise OpenRouterAPIError(f"OpenRouter HTTP {status_code}: {hse.response.text}") from hse

            except Exception as e:
                duration = time.perf_counter() - t_attempt_start
                logger.warning(
                    f"\n[LLM ATTEMPT]\n"
                    f"attempt={attempt_num}\n"
                    f"model={self.model}\n"
                    f"duration={duration:.3f}s\n"
                    f"status=error\n"
                    f"success=false"
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(1.0)
                    continue
                raise OpenRouterAPIError(f"OpenRouter generation error: {str(e)}") from e
