"""Structure Analyzer for detecting headings, sections, paragraphs, lists, and tables."""

import re
from typing import List, Tuple
from app.knowledge.exceptions import StructureAnalyzerError
from app.knowledge.models.document import Document
from app.knowledge.models.section import Section
from app.utils.logging import logger


class StructureAnalyzer:
    """Analyzes a Document object to identify structural elements (headings, lists, tables, paragraphs) in reading order."""

    # Heading patterns
    MARKDOWN_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
    NUMBERED_HEADING_RE = re.compile(r"^(?:Section|Chapter|Part)?\s*(\d+(?:\.\d+)*)\s*[:.-]?\s+(.+)$", re.IGNORECASE)
    EXPLICIT_HEADER_RE = re.compile(
        r"^(?:Executive Summary|Table of Contents|Introduction|Background|Methodology|Results|Discussion|Conclusion|References|Appendix|Overview|Financial Performance|Security Guidelines)\b",
        re.IGNORECASE,
    )

    # List patterns
    BULLET_LIST_RE = re.compile(r"^\s*[\-\*•–—]\s+(.+)$")
    NUMBERED_LIST_RE = re.compile(r"^\s*(?:\d+[\.\)]|\([a-z0-9]+\))\s+(.+)$", re.IGNORECASE)

    # Table pattern (contains pipe separators or multiple tab/space-separated tabular columns)
    TABLE_ROW_RE = re.compile(r"\||(?:\s{3,}\S+){2,}")

    @classmethod
    def analyze(cls, document: Document) -> List[Section]:
        """Parses document pages to detect and classify structural sections preserving reading order.

        Args:
            document (Document): Cleaned Document object from Phase 1.

        Returns:
            List[Section]: Flat ordered list of Section domain objects.

        Raises:
            StructureAnalyzerError: If structural analysis fails.
        """
        if not document.pages:
            logger.warning(f"StructureAnalyzer received Document '{document.filename}' with 0 pages.")
            return []

        logger.info(f"Analyzing document structure for '{document.filename}' ({document.total_pages} pages)...")

        sections: List[Section] = []
        global_reading_order = 0

        try:
            for page in document.pages:
                page_sections, global_reading_order = cls._analyze_page(
                    page_text=page.text,
                    page_number=page.page_number,
                    start_order=global_reading_order,
                )
                sections.extend(page_sections)

            logger.info(
                f"Completed structure analysis for '{document.filename}'. "
                f"Extracted {len(sections)} structural sections across {document.total_pages} pages."
            )
            return sections

        except Exception as e:
            logger.error(f"Structure analysis failed for '{document.filename}': {e}")
            raise StructureAnalyzerError(f"Failed to analyze structure of '{document.filename}': {str(e)}") from e

    @classmethod
    def _analyze_page(cls, page_text: str, page_number: int, start_order: int) -> Tuple[List[Section], int]:
        """Analyzes single page text line-by-line into typed sections.

        Args:
            page_text (str): Cleaned page text.
            page_number (int): 1-indexed page number.
            start_order (int): Initial reading order offset.

        Returns:
            Tuple[List[Section], int]: Tuple of (extracted sections, next available reading_order).
        """
        sections: List[Section] = []
        reading_order = start_order

        if not page_text.strip():
            return sections, reading_order

        raw_lines = [line.strip() for line in page_text.split("\n")]
        
        # Buffer for grouping paragraph lines or consecutive list/table lines
        current_type: str | None = None
        current_lines: List[str] = []
        current_meta: dict = {}

        def flush_buffer():
            nonlocal reading_order, current_type, current_lines, current_meta
            if not current_lines or not current_type:
                return

            content = "\n".join(current_lines).strip()
            if not content:
                current_lines = []
                current_type = None
                return

            title = current_meta.get("title") or f"{current_type.capitalize()} (Page {page_number})"
            level = current_meta.get("level", 4)

            sections.append(
                Section(
                    title=title,
                    section_type=current_type,
                    level=level,
                    content=content,
                    page_number=page_number,
                    reading_order=reading_order,
                )
            )
            reading_order += 1
            current_lines = []
            current_type = None
            current_meta = {}

        i = 0
        while i < len(raw_lines):
            line = raw_lines[i]
            if not line:
                flush_buffer()
                i += 1
                continue

            # Check for Heading
            is_heading, title, level = cls._detect_heading(line)
            if is_heading:
                flush_buffer()
                sections.append(
                    Section(
                        title=title,
                        section_type="heading",
                        level=level,
                        content=line,
                        page_number=page_number,
                        reading_order=reading_order,
                    )
                )
                reading_order += 1
                i += 1
                continue

            # Check for Table row
            if cls.TABLE_ROW_RE.search(line):
                if current_type != "table":
                    flush_buffer()
                    current_type = "table"
                    current_meta = {"title": f"Table (Page {page_number})", "level": 3}
                current_lines.append(line)
                i += 1
                continue

            # Check for List item
            if cls.BULLET_LIST_RE.match(line) or cls.NUMBERED_LIST_RE.match(line):
                if current_type != "list":
                    flush_buffer()
                    current_type = "list"
                    current_meta = {"title": f"List Block (Page {page_number})", "level": 3}
                current_lines.append(line)
                i += 1
                continue

            # Regular Paragraph line
            if current_type != "paragraph":
                flush_buffer()
                current_type = "paragraph"
                current_meta = {"title": f"Paragraph (Page {page_number})", "level": 4}
            current_lines.append(line)
            i += 1

        flush_buffer()
        return sections, reading_order

    @classmethod
    def _detect_heading(cls, line: str) -> Tuple[bool, str, int]:
        """Determines if a single line is a heading and determines its hierarchy level.

        Returns:
            Tuple[bool, str, int]: (is_heading, heading_title, hierarchy_level)
        """
        # Markdown heading match (# Heading)
        md_match = cls.MARKDOWN_HEADING_RE.match(line)
        if md_match:
            hashes, title = md_match.groups()
            level = min(6, len(hashes))
            return True, title.strip(), level

        # Numbered heading match (Section 1: Executive Summary or 1.1 Overview)
        num_match = cls.NUMBERED_HEADING_RE.match(line)
        if num_match and len(line) < 100:
            num_prefix, title = num_match.groups()
            depth = num_prefix.count(".") + 1
            level = min(4, depth)
            return True, line.strip(), level

        # Explicit header keywords match
        if cls.EXPLICIT_HEADER_RE.match(line) and len(line) < 80:
            return True, line.strip(), 1

        # Short uppercase or title-case line without trailing period
        if len(line) < 60 and not line.endswith("."):
            if line.isupper() and len(line) > 3:
                return True, line.strip(), 1
            if line.istitle() and len(line) > 3 and not cls.BULLET_LIST_RE.match(line) and not cls.NUMBERED_LIST_RE.match(line):
                return True, line.strip(), 2

        return False, "", 1
