"""LLMService wrapping LLMGateway for clean architectural decoupling."""

from typing import Any, Optional
from app.config import settings
from app.knowledge.rag.llm_gateway import LLMGateway


class LLMService:
    """Service wrapping LLMGateway for text completion operations."""

    def __init__(
        self,
        api_key: str = settings.OPENROUTER_API_KEY,
        model: str = settings.PRIMARY_MODEL,
        fallback_model: Optional[str] = None,
        base_url: str = settings.OPENROUTER_BASE_URL,
        timeout_seconds: float = settings.LLM_TIMEOUT_SECONDS,
        max_retries: int = settings.LLM_MAX_RETRIES,
        max_tokens: int = settings.LLM_MAX_TOKENS,
        gateway: Optional[LLMGateway] = None,
    ):
        """Initializes LLMService with injected or default LLMGateway."""
        self.gateway = gateway or LLMGateway(
            api_key=api_key,
            primary_model=model,
            fallback_model=fallback_model,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            max_tokens=max_tokens,
        )

    def generate(
        self,
        prompt: str,
        raise_on_missing_key: bool = False,
        request_id: Optional[str] = None,
        tracker: Optional[Any] = None,
    ) -> str:
        """Executes synchronous text generation via LLMGateway."""
        return self.gateway.generate(prompt, request_id=request_id, tracker=tracker)

    async def generate_async(
        self,
        prompt: str,
        raise_on_missing_key: bool = False,
        request_id: Optional[str] = None,
        tracker: Optional[Any] = None,
    ) -> str:
        """Executes asynchronous text generation via LLMGateway."""
        return await self.gateway.generate_async(prompt, request_id=request_id, tracker=tracker)

    def get_status(self):
        """Returns scheduler telemetry status report."""
        return self.gateway.scheduler.get_status()

