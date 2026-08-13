"""Deterministic, lightweight QueryDecomposer for multi-intent RAG retrieval."""

import re
from typing import List
from app.utils.logging import logger

# Recognized domain keyword groups for multi-intent detection
DOMAIN_GROUPS = {
    "ownership": [
        "ownership", "owner", "owners", "shareholding", "promoter",
        "promoters", "share capital", "equity holding", "shareholders"
    ],
    "marketing": [
        "marketing", "marketing strategy", "marketing strategies",
        "sales strategy", "advertising", "distribution channel", "sales promotion"
    ],
    "products": [
        "product", "products", "major products", "services", "offerings", "business segments"
    ],
    "financials": [
        "revenue", "profit", "ebitda", "financials", "sales revenue", "income", "margin", "pat", "balance sheet"
    ],
    "governance": [
        "director", "directors", "board of directors", "responsibilities", "management", "executives", "kmp"
    ],
    "sustainability": [
        "esg", "sustainability", "emissions", "carbon", "waste management", "renewable energy"
    ]
}


class QueryDecomposer:
    """Lightweight, deterministic query decomposer that splits multi-intent queries into standalone retrieval subqueries without LLM calls."""

    @staticmethod
    def _detect_domains(text: str) -> List[str]:
        """Detects matching domain groups present in the query text."""
        text_lower = text.lower()
        matched_domains = []
        for domain, keywords in DOMAIN_GROUPS.items():
            for kw in keywords:
                # Match full word / phrase boundaries
                pattern = r'\b' + re.escape(kw) + r'\b'
                if re.search(pattern, text_lower):
                    matched_domains.append(domain)
                    break
        return matched_domains

    @classmethod
    def decompose(cls, query: str) -> List[str]:
        """Decomposes a user query into up to 3 standalone retrieval subqueries.

        Args:
            query (str): Input query string.

        Returns:
            List[str]: List of 1 to 3 standalone subqueries.
        """
        if not query or not query.strip():
            return [query]

        clean_query = query.strip()

        # Rule 1: Check for multiple question marks
        if "?" in clean_query:
            parts = [p.strip() + "?" for p in clean_query.split("?") if p.strip()]
            if len(parts) > 1:
                # Standardize questions
                subqueries = []
                for p in parts:
                    clean_p = p.lstrip("?").strip()
                    if clean_p:
                        # Fix trailing double question marks if any
                        clean_p = re.sub(r'\?+$', '?', clean_p)
                        if not clean_p.endswith("?"):
                            clean_p += "?"
                        subqueries.append(clean_p)

                if 1 < len(subqueries) <= 3:
                    logger.info(f"[QUERY DECOMPOSITION] Split by question marks into {len(subqueries)} subqueries.")
                    return subqueries

        # Rule 2: Split on explicit conjunctions between independent question clauses
        # Examples: "Who are the current owners of the company and what are its marketing strategies?"
        split_pattern = r'\b(?:and\s+(?:what|who|how|tell\s+me|explain|which)|,\s*(?:tell\s+me|what|who|how|which))\b'
        match = re.search(split_pattern, clean_query, flags=re.IGNORECASE)
        if match:
            part1 = clean_query[:match.start()].strip()
            part2 = clean_query[match.start():].strip()

            # Clean leading conjunctions from part2
            part2 = re.sub(r'^(?:and|,)\s*', '', part2, flags=re.IGNORECASE).strip()

            # Ensure proper question capitalization and mark
            if part1 and not part1.endswith("?"):
                part1 += "?"
            if part2 and not part2.endswith("?"):
                part2 += "?"

            # Make part2 capital start
            part2 = part2[0].upper() + part2[1:] if part2 else part2

            if part1 and part2:
                # Check that part1 and part2 represent distinct domains or substantive queries
                domains_p1 = cls._detect_domains(part1)
                domains_p2 = cls._detect_domains(part2)

                # If domains are distinct or both non-empty and different
                if not domains_p1 or not domains_p2 or domains_p1 != domains_p2:
                    subqueries = [part1, part2]
                    logger.info(f"[QUERY DECOMPOSITION] Split by clause conjunction into {len(subqueries)} subqueries.")
                    return subqueries

        # Rule 3: Check for multi-domain topic lists or comparisons across distinct domains
        # Example: "Tell me about ownership, marketing strategy and major products."
        # Example: "Compare the company's ownership structure and marketing strategy."
        matched_domains = cls._detect_domains(clean_query)

        # Only split if 2 or 3 DIFFERENT domains are present (e.g. Ownership + Marketing + Products)
        if len(matched_domains) >= 2:
            # Check if all matched domains are distinct
            unique_domains = list(dict.fromkeys(matched_domains))
            if len(unique_domains) >= 2:
                # Cap at 3 domains
                target_domains = unique_domains[:3]
                subqueries = []

                domain_labels = {
                    "ownership": "the company's ownership structure and shareholding details",
                    "marketing": "the company's marketing and sales strategies",
                    "products": "the company's major products and services",
                    "financials": "the company's financial performance and revenue",
                    "governance": "the company's board of directors and management",
                    "sustainability": "the company's ESG and sustainability practices",
                }

                for d in target_domains:
                    label = domain_labels.get(d, f"the company's {d}")
                    subqueries.append(f"What are details regarding {label}?")

                logger.info(f"[QUERY DECOMPOSITION] Extracted {len(subqueries)} distinct domain subqueries: {unique_domains}")
                return subqueries

        # Rule 4: Default single intent fallback
        return [clean_query]
