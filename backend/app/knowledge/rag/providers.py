"""Provider Adapters isolating provider-specific HTTP/API execution details."""

from abc import ABC, abstractmethod
import json
import time
from typing import Any, Dict, Optional, Tuple
import httpx

from app.config import settings
from app.knowledge.exceptions import LLMServiceError, LLMTimeoutError, OpenRouterAPIError
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
    import re
    if "choices" not in data or not data["choices"]:
        raise OpenRouterAPIError("OpenRouter API returned empty choices list.")

    choice = data["choices"][0]
    message = choice.get("message", {})
    finish_reason = choice.get("finish_reason", "unknown")

    content = message.get("content", "") or ""

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



class LLMProvider(ABC):
    """Abstract interface for LLM provider execution adapters."""

    @abstractmethod
    async def generate_async(
        self,
        prompt: str,
        model: str,
        api_key: str,
        timeout_seconds: float = settings.LLM_TIMEOUT_SECONDS,
        max_retries: int = settings.LLM_MAX_RETRIES,
        max_tokens: int = settings.LLM_MAX_TOKENS,
    ) -> str:
        """Asynchronously executes text completion."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        model: str,
        api_key: str,
        timeout_seconds: float = settings.LLM_TIMEOUT_SECONDS,
        max_retries: int = settings.LLM_MAX_RETRIES,
        max_tokens: int = settings.LLM_MAX_TOKENS,
    ) -> str:
        """Synchronously executes text completion."""
        pass


class NemotronProviderAdapter(LLMProvider):
    """Adapter for OpenRouter / Nemotron completions reusing shared HTTP connection pool."""

    def __init__(self, base_url: str = settings.OPENROUTER_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def _build_payload(self, prompt: str, model: str, max_tokens: int, stream: bool = False) -> Dict[str, Any]:
        return {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": max_tokens,
            "stream": stream,
            "reasoning": {"max_tokens": 0},
        }

    def _build_headers(self, api_key: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://techonomy.ai",
            "X-Title": "Techonomy Enterprise Knowledge Platform",
            "Content-Type": "application/json",
        }

    async def generate_async(
        self,
        prompt: str,
        model: str,
        api_key: str,
        timeout_seconds: float = settings.LLM_TIMEOUT_SECONDS,
        max_retries: int = settings.LLM_MAX_RETRIES,
        max_tokens: int = settings.LLM_MAX_TOKENS,
    ) -> str:
        if not api_key:
            raise OpenRouterAPIError("OpenRouter API key is missing. OPENROUTER_API_KEY environment variable must be configured.")

        url = f"{self.base_url}/chat/completions"
        headers = self._build_headers(api_key)
        payload = self._build_payload(prompt, model, max_tokens)
        client = get_shared_async_client()

        last_exc = None
        for attempt in range(max_retries + 1):
            t_start = time.perf_counter()
            try:
                response = await client.post(url, headers=headers, json=payload, timeout=timeout_seconds)
                duration = time.perf_counter() - t_start
                response.raise_for_status()
                data = response.json()
                clean_answer, metrics = extract_clean_answer(data)
                return clean_answer
            except httpx.TimeoutException as exc:
                last_exc = LLMTimeoutError(f"Nemotron API request timed out after {timeout_seconds}s.")
                if attempt < max_retries:
                    import asyncio
                    await asyncio.sleep(0.5 * (2 ** attempt))
                    continue
            except Exception as exc:
                last_exc = exc
                if attempt < max_retries:
                    import asyncio
                    await asyncio.sleep(0.5 * (2 ** attempt))
                    continue

        if isinstance(last_exc, Exception):
            raise last_exc
        raise OpenRouterAPIError("LLM generation failed across configured retries.")

    def generate(
        self,
        prompt: str,
        model: str,
        api_key: str,
        timeout_seconds: float = settings.LLM_TIMEOUT_SECONDS,
        max_retries: int = settings.LLM_MAX_RETRIES,
        max_tokens: int = settings.LLM_MAX_TOKENS,
    ) -> str:
        if not api_key:
            raise OpenRouterAPIError("OpenRouter API key is missing. OPENROUTER_API_KEY environment variable must be configured.")

        url = f"{self.base_url}/chat/completions"
        headers = self._build_headers(api_key)
        payload = self._build_payload(prompt, model, max_tokens)
        client = get_shared_sync_client()

        last_exc = None
        for attempt in range(max_retries + 1):
            t_start = time.perf_counter()
            try:
                response = client.post(url, headers=headers, json=payload, timeout=timeout_seconds)
                duration = time.perf_counter() - t_start
                response.raise_for_status()
                data = response.json()
                clean_answer, metrics = extract_clean_answer(data)
                return clean_answer
            except httpx.TimeoutException as exc:
                last_exc = LLMTimeoutError(f"Nemotron API request timed out after {timeout_seconds}s.")
                if attempt < max_retries:
                    time.sleep(0.5 * (2 ** attempt))
                    continue
            except Exception as exc:
                last_exc = exc
                if attempt < max_retries:
                    time.sleep(0.5 * (2 ** attempt))
                    continue

        if isinstance(last_exc, Exception):
            raise last_exc
        raise OpenRouterAPIError("LLM generation failed across configured retries.")


class GeminiProviderAdapter(LLMProvider):
    """Adapter for Google Gemini API completions using shared HTTP connection pool."""

    def __init__(self, base_url: str = "https://generativelanguage.googleapis.com/v1beta"):
        self.base_url = base_url.rstrip("/")

    def _build_payload(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        return {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": max_tokens,
            }
        }

    async def generate_async(
        self,
        prompt: str,
        model: str,
        api_key: str,
        timeout_seconds: float = settings.LLM_TIMEOUT_SECONDS,
        max_retries: int = settings.LLM_MAX_RETRIES,
        max_tokens: int = settings.LLM_MAX_TOKENS,
    ) -> str:
        if not api_key:
            raise LLMServiceError("Gemini API key is missing.")

        url = f"{self.base_url}/models/{model}:generateContent?key={api_key}"
        payload = self._build_payload(prompt, max_tokens)
        client = get_shared_async_client()

        last_exc = None
        for attempt in range(max_retries + 1):
            t_start = time.perf_counter()
            try:
                response = await client.post(url, json=payload, timeout=timeout_seconds)
                duration = time.perf_counter() - t_start
                response.raise_for_status()
                data = response.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    raise LLMServiceError("Gemini API returned no candidates.")
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    raise LLMServiceError("Gemini API returned empty response parts.")
                return parts[0].get("text", "").strip()
            except httpx.TimeoutException as exc:
                last_exc = LLMTimeoutError(f"Gemini API request timed out after {timeout_seconds}s.")
                if attempt < max_retries:
                    import asyncio
                    await asyncio.sleep(0.5 * (2 ** attempt))
                    continue
            except Exception as exc:
                last_exc = exc
                if attempt < max_retries:
                    import asyncio
                    await asyncio.sleep(0.5 * (2 ** attempt))
                    continue

        if isinstance(last_exc, Exception):
            raise last_exc
        raise LLMServiceError("Gemini generation failed across configured retries.")

    def generate(
        self,
        prompt: str,
        model: str,
        api_key: str,
        timeout_seconds: float = settings.LLM_TIMEOUT_SECONDS,
        max_retries: int = settings.LLM_MAX_RETRIES,
        max_tokens: int = settings.LLM_MAX_TOKENS,
    ) -> str:
        if not api_key:
            raise LLMServiceError("Gemini API key is missing.")

        url = f"{self.base_url}/models/{model}:generateContent?key={api_key}"
        payload = self._build_payload(prompt, max_tokens)
        client = get_shared_sync_client()

        last_exc = None
        for attempt in range(max_retries + 1):
            t_start = time.perf_counter()
            try:
                response = client.post(url, json=payload, timeout=timeout_seconds)
                duration = time.perf_counter() - t_start
                response.raise_for_status()
                data = response.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    raise LLMServiceError("Gemini API returned no candidates.")
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    raise LLMServiceError("Gemini API returned empty response parts.")
                return parts[0].get("text", "").strip()
            except httpx.TimeoutException as exc:
                last_exc = LLMTimeoutError(f"Gemini API request timed out after {timeout_seconds}s.")
                if attempt < max_retries:
                    time.sleep(0.5 * (2 ** attempt))
                    continue
            except Exception as exc:
                last_exc = exc
                if attempt < max_retries:
                    time.sleep(0.5 * (2 ** attempt))
                    continue

        if isinstance(last_exc, Exception):
            raise last_exc
        raise LLMServiceError("Gemini generation failed across configured retries.")
