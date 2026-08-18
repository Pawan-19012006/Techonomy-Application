"""PromptBuilder module constructing grounded RAG prompts for Techonomy."""

from pathlib import Path
from typing import List, Optional
from app.config import settings
from app.knowledge.exceptions import PromptBuilderError
from app.knowledge.models.search_result import SearchResult
from app.utils.logging import logger

SYSTEM_PROMPT_PATH = settings.BASE_DIR / "app" / "prompts" / "system_prompt.txt"


class PromptBuilder:
    """Constructs grounded production prompts incorporating system instructions, retrieved context chunks, and user query."""

    DEFAULT_SYSTEM_MESSAGE = (
        "You are Techonomy Intelligence Assistant.\n"
        "You answer ONLY using the supplied company documents.\n"
        "Never invent information.\n"
        "If the answer is not contained inside the retrieved context, clearly state that the provided documents do not contain sufficient information.\n"
        "Always cite document names and page numbers whenever possible."
    )

    def __init__(self, system_prompt_path: Optional[Path] = SYSTEM_PROMPT_PATH):
        """Initializes PromptBuilder with optional path to system prompt text file."""
        self.system_prompt_path = system_prompt_path
        self._system_message: Optional[str] = None

    def get_system_message(self) -> str:
        """Reads system message from file or falls back to default system prompt constant."""
        if self._system_message is not None:
            return self._system_message

        if self.system_prompt_path and self.system_prompt_path.exists():
            try:
                content = self.system_prompt_path.read_text(encoding="utf-8").strip()
                if content:
                    self._system_message = content
                    return self._system_message
            except Exception as e:
                logger.warning(f"Failed to read system prompt file '{self.system_prompt_path}': {e}")

        self._system_message = self.DEFAULT_SYSTEM_MESSAGE
        return self._system_message

    def format_context_chunks(self, chunks: List[SearchResult]) -> str:
        """Formats retrieved SearchResult chunks into structured context text (Company Evidence ONLY)."""
        company_chunks = [
            c for c in chunks
            if getattr(c, "document_type", "company") == "company" and getattr(c, "visibility", "user_visible") == "user_visible"
        ]

        if not company_chunks:
            return "No relevant company document context found."

        formatted_blocks = []
        for idx, chunk in enumerate(company_chunks, start=1):
            pages_str = ", ".join(str(p) for p in chunk.page_numbers) if chunk.page_numbers else "N/A"
            block = (
                f"Chunk {idx}\n"
                f"Doc: {chunk.document_name} | Page(s): {pages_str} | Section: {chunk.section_title}\n"
                f"{chunk.content.strip()}"
            )
            formatted_blocks.append(block)

        return "\n\n".join(formatted_blocks)

    def build_prompt(self, query: str, chunks: List[SearchResult]) -> str:
        """Generates complete grounded prompt according to exact platform specifications.

        Structure:
        SYSTEM MESSAGE
        ------------------------------------
        Retrieved Context
        Chunk 1
        Chunk 2
        ...
        ------------------------------------
        User Question
        """
        if not query or not query.strip():
            raise PromptBuilderError("User question query cannot be empty.")

        system_msg = self.get_system_message()
        context_str = self.format_context_chunks(chunks)

        prompt = (
            f"{system_msg}\n\n"
            f"------------------------------------\n"
            f"Retrieved Context\n\n"
            f"{context_str}\n\n"
            f"------------------------------------\n"
            f"User Question\n"
            f"{query.strip()}"
        )
        return prompt
