"""Provider Adapters isolating provider-specific HTTP/API execution details and streaming generators."""

from abc import ABC, abstractmethod
import json
import time
from typing import Any, AsyncGenerator, Dict, Optional, Tuple
import httpx

from app.config import settings
from app.knowledge.exceptions import LLMServiceError, LLMTimeoutError, OpenRouterAPIError
from app.utils.logging import logger

_shared_async_client: Optional[httpx.AsyncClient] = None
_shared_sync_client: Optional[httpx.Client] = None


def get_shared_async_client() -> httpx.AsyncClient:
    """Returns or creates shared httpx.AsyncClient with connection pooling."""
    global _shared_async_client
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if _shared_async_client is None or _shared_async_client.is_closed or getattr(_shared_async_client, "_loop", None) != loop:
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
        _shared_async_client = httpx.AsyncClient(
            limits=limits,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        setattr(_shared_async_client, "_loop", loop)
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


def extract_clean_answer(data: Dict[str, Any], max_tokens: int = settings.LLM_MAX_TOKENS) -> Tuple[str, Dict[str, Any]]:
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

    if finish_reason == "length":
        logger.warning(f"[LLM_TRUNCATION_WARNING] OpenRouter response hit token ceiling (finish_reason=length, max_tokens={max_tokens}).")

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


def _sanitize_credential_error(exc: Exception, api_key: str) -> Exception:
    """Masks raw API keys in exception messages to ensure credential privacy."""
    if not api_key:
        return exc
    err_str = str(exc)
    if api_key in err_str:
        clean_str = err_str.replace(api_key, "[REDACTED_API_KEY]")
        return LLMServiceError(f"Provider API Exception: {clean_str}")
    return exc


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

    @abstractmethod
    async def generate_stream_async(
        self,
        prompt: str,
        model: str,
        api_key: str,
        timeout_seconds: float = settings.LLM_TIMEOUT_SECONDS,
        max_tokens: int = settings.LLM_MAX_TOKENS,
    ) -> AsyncGenerator[Tuple[str, Optional[str]], None]:
        """Yields (content_chunk, finish_reason) tuples for progressive streaming."""
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
            try:
                response = await client.post(url, headers=headers, json=payload, timeout=timeout_seconds)
                response.raise_for_status()
                data = response.json()
                clean_answer, _ = extract_clean_answer(data, max_tokens=max_tokens)
                return clean_answer
            except httpx.TimeoutException:
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
            try:
                response = client.post(url, headers=headers, json=payload, timeout=timeout_seconds)
                response.raise_for_status()
                data = response.json()
                clean_answer, _ = extract_clean_answer(data, max_tokens=max_tokens)
                return clean_answer
            except httpx.TimeoutException:
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

    async def generate_stream_async(
        self,
        prompt: str,
        model: str,
        api_key: str,
        timeout_seconds: float = settings.LLM_TIMEOUT_SECONDS,
        max_tokens: int = settings.LLM_MAX_TOKENS,
    ) -> AsyncGenerator[Tuple[str, Optional[str]], None]:
        if not api_key:
            raise OpenRouterAPIError("OpenRouter API key is missing. OPENROUTER_API_KEY environment variable must be configured.")

        url = f"{self.base_url}/chat/completions"
        headers = self._build_headers(api_key)
        payload = self._build_payload(prompt, model, max_tokens, stream=True)
        client = get_shared_async_client()

        async with client.stream("POST", url, headers=headers, json=payload, timeout=timeout_seconds) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data_json = json.loads(data_str)
                        choices = data_json.get("choices", [])
                        if not choices:
                            continue
                        choice = choices[0]
                        delta = choice.get("delta", {})
                        finish_reason = choice.get("finish_reason")

                        if "reasoning" in delta or "thinking" in delta or "reasoning_details" in delta:
                            continue

                        content_chunk = delta.get("content")
                        if content_chunk or finish_reason:
                            yield (content_chunk or "", finish_reason)
                    except Exception:
                        continue


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

    def _extract_gemini_text(self, data: Dict[str, Any], max_tokens: int) -> Tuple[str, Optional[str]]:
        candidates = data.get("candidates", [])
        if not candidates:
            raise LLMServiceError("Gemini API returned no candidates.")
        candidate = candidates[0]
        finish_reason = candidate.get("finishReason")
        parts = candidate.get("content", {}).get("parts", [])
        if not parts:
            raise LLMServiceError("Gemini API returned empty response parts.")

        text = parts[0].get("text", "").strip()
        if finish_reason == "MAX_TOKENS":
            logger.warning(f"[LLM_TRUNCATION_WARNING] Gemini response hit token ceiling (finishReason=MAX_TOKENS, max_tokens={max_tokens}).")
            text += f"\n\n*(Note: Output reached configured token limit of {max_tokens}. Ask a follow-up question for remaining details.)*"

        return text, finish_reason

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
            try:
                response = await client.post(url, json=payload, timeout=timeout_seconds)
                response.raise_for_status()
                data = response.json()
                text, _ = self._extract_gemini_text(data, max_tokens)
                return text
            except httpx.TimeoutException:
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
            raise _sanitize_credential_error(last_exc, api_key)
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
            try:
                response = client.post(url, json=payload, timeout=timeout_seconds)
                response.raise_for_status()
                data = response.json()
                text, _ = self._extract_gemini_text(data, max_tokens)
                return text
            except httpx.TimeoutException:
                last_exc = LLMTimeoutError(f"Gemini API request timed out after {timeout_seconds}s.")
                if attempt < max_retries:
                    time.sleep(0.5 * (2 ** attempt))
                    continue
            except Exception as exc:
                last_exc = _sanitize_credential_error(exc, api_key)
                if attempt < max_retries:
                    time.sleep(0.5 * (2 ** attempt))
                    continue

        if isinstance(last_exc, Exception):
            raise _sanitize_credential_error(last_exc, api_key)
        raise LLMServiceError("Gemini generation failed across configured retries.")

    async def generate_stream_async(
        self,
        prompt: str,
        model: str,
        api_key: str,
        timeout_seconds: float = settings.LLM_TIMEOUT_SECONDS,
        max_tokens: int = settings.LLM_MAX_TOKENS,
    ) -> AsyncGenerator[Tuple[str, Optional[str]], None]:
        if not api_key:
            raise LLMServiceError("Gemini API key is missing.")

        url = f"{self.base_url}/models/{model}:streamGenerateContent?alt=sse&key={api_key}"
        payload = self._build_payload(prompt, max_tokens)
        client = get_shared_async_client()

        try:
            async with client.stream("POST", url, json=payload, timeout=timeout_seconds) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if not data_str or data_str == "[DONE]":
                            continue
                        try:
                            data_json = json.loads(data_str)
                            # Handle standard Gemini SSE candidate payload
                            candidates = data_json.get("candidates", [])
                            if candidates:
                                candidate = candidates[0]
                                finish_reason = candidate.get("finishReason")
                                parts = candidate.get("content", {}).get("parts", [])
                                chunk_text = parts[0].get("text", "") if parts else ""
                                if chunk_text or finish_reason:
                                    yield (chunk_text, finish_reason)
                                continue

                            # Handle fallback/mock choices payload format
                            choices = data_json.get("choices", [])
                            if choices:
                                choice = choices[0]
                                delta = choice.get("delta", {})
                                finish_reason = choice.get("finish_reason")
                                chunk_text = delta.get("content", "")
                                if chunk_text or finish_reason:
                                    yield (chunk_text, finish_reason)
                        except Exception:
                            continue
        except Exception as exc:
            raise _sanitize_credential_error(exc, api_key)
