"""Text Cleaner for normalizing text and removing headers/footers in Document objects."""

import re
from typing import List, Set, Tuple
from app.knowledge.exceptions import TextCleanerError
from app.knowledge.models.document import Document
from app.knowledge.models.page import Page
from app.utils.logging import logger


class TextCleaner:
    """Cleans and normalizes extracted page text across Document objects."""

    @classmethod
    def clean(cls, document: Document) -> Document:
        """Cleans document text page-by-page while preserving page structure and numbering.

        Args:
            document (Document): Raw Document object containing extracted Page objects.

        Returns:
            Document: New Document object containing cleaned Page objects.

        Raises:
            TextCleanerError: If text cleaning encounters an unexpected error.
        """
        if not document.pages:
            logger.warning(f"TextCleaner received Document '{document.filename}' with 0 pages.")
            return document

        logger.info(f"Starting text cleaning for Document '{document.filename}' ({document.total_characters} chars)...")

        try:
            # 1. Detect repeated headers and footers across pages
            headers_to_remove, footers_to_remove = cls._detect_headers_footers(document.pages)

            cleaned_pages: List[Page] = []
            chars_before = 0
            chars_after = 0

            for page in document.pages:
                chars_before += len(page.text)
                cleaned_text = cls._clean_page_text(
                    page.text,
                    headers_to_remove=headers_to_remove,
                    footers_to_remove=footers_to_remove
                )
                chars_after += len(cleaned_text)

                page_meta = dict(page.metadata)
                page_meta["cleaned_char_count"] = len(cleaned_text)

                cleaned_pages.append(
                    Page(
                        page_number=page.page_number,
                        text=cleaned_text,
                        metadata=page_meta
                    )
                )

            # Construct new cleaned Document
            cleaned_doc = Document(
                id=document.id,
                filename=document.filename,
                title=document.title,
                file_type=document.file_type,
                total_pages=len(cleaned_pages),
                pages=cleaned_pages,
                metadata={
                    **document.metadata,
                    "cleaned": True,
                    "raw_char_count": chars_before,
                    "cleaned_char_count": chars_after,
                    "chars_removed": chars_before - chars_after,
                }
            )

            diff_pct = ((chars_before - chars_after) / chars_before * 100) if chars_before > 0 else 0
            logger.info(
                f"Completed text cleaning for '{document.filename}'. "
                f"Characters: {chars_before} -> {chars_after} (removed {diff_pct:.2f}% noisy text)."
            )
            return cleaned_doc

        except Exception as e:
            logger.error(f"Failed to clean Document '{document.filename}': {e}")
            raise TextCleanerError(f"Text cleaning failed for Document '{document.filename}': {str(e)}") from e

    @classmethod
    def _clean_page_text(
        cls,
        raw_text: str,
        headers_to_remove: Set[str],
        footers_to_remove: Set[str]
    ) -> str:
        """Cleans text string of a single page.

        Args:
            raw_text (str): Raw extracted page text.
            headers_to_remove (Set[str]): Set of detected repeated header lines.
            footers_to_remove (Set[str]): Set of detected repeated footer lines.

        Returns:
            str: Cleaned text string.
        """
        if not raw_text:
            return ""

        # Normalize line breaks
        text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
        
        # Replace non-breaking spaces and zero-width spaces
        text = text.replace("\xa0", " ").replace("\u200b", "")

        lines = [line.strip() for line in text.split("\n")]

        # Filter out detected repeated headers/footers
        filtered_lines: List[str] = []
        for line in lines:
            normalized_line = re.sub(r"\s+", " ", line).strip()
            if normalized_line in headers_to_remove or normalized_line in footers_to_remove:
                continue
            filtered_lines.append(line)

        # Collapse multiple horizontal spaces within each line
        processed_lines = [re.sub(r"[ \t]+", " ", line) for line in filtered_lines]

        # Join lines back
        joined_text = "\n".join(processed_lines)

        # Collapse 3+ consecutive newlines to 2 newlines (preserving clean paragraph breaks)
        cleaned = re.sub(r"\n{3,}", "\n\n", joined_text)

        return cleaned.strip()

    @classmethod
    def _detect_headers_footers(cls, pages: List[Page], threshold: float = 0.75) -> Tuple[Set[str], Set[str]]:
        """Identifies header and footer lines that repeat across >= threshold proportion of pages.

        Args:
            pages (List[Page]): Document page list.
            threshold (float): Proportional frequency cutoff (0.75 = 75% of pages).

        Returns:
            Tuple[Set[str], Set[str]]: Tuple of (detected_headers, detected_footers).
        """
        if len(pages) < 3:
            # Not enough pages to reliably detect repeating headers/footers
            return set(), set()

        header_counts: dict[str, int] = {}
        footer_counts: dict[str, int] = {}
        min_occurrences = max(2, int(len(pages) * threshold))

        for page in pages:
            lines = [re.sub(r"\s+", " ", line).strip() for line in page.text.split("\n") if line.strip()]
            if not lines:
                continue

            # First 2 non-empty lines candidate headers
            for h_line in lines[:2]:
                if len(h_line) > 3 and not h_line.isdigit():
                    header_counts[h_line] = header_counts.get(h_line, 0) + 1

            # Last 2 non-empty lines candidate footers
            for f_line in lines[-2:]:
                if len(f_line) > 3 and not f_line.isdigit():
                    footer_counts[f_line] = footer_counts.get(f_line, 0) + 1

        headers = {line for line, count in header_counts.items() if count >= min_occurrences}
        footers = {line for line, count in footer_counts.items() if count >= min_occurrences}

        if headers:
            logger.debug(f"Detected repeated header lines: {headers}")
        if footers:
            logger.debug(f"Detected repeated footer lines: {footers}")

        return headers, footers
