"""Dynamic Concept & Synonym Expansion Layer for broadening domain concepts in RAG queries."""

import re
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field


class ConceptExpansion(BaseModel):
    """Container for expanded concepts, synonyms, and subqueries."""

    primary_concepts: List[str] = Field(default_factory=list, description="Extracted primary business concepts")
    expanded_terms: List[str] = Field(default_factory=list, description="Synonyms and related metric terms")
    generated_subqueries: List[str] = Field(default_factory=list, description="Targeted vector search queries")


class ConceptExpander:
    """Dynamically expands user queries into domain-specific business concept terms and target subqueries."""

    # Extensible taxonomy of business domains, metrics, and synonyms
    CONCEPT_TAXONOMY: Dict[str, List[str]] = {
        "profitability": [
            "net profit", "PAT", "profit after tax", "EBITDA", "EBIT", "operating profit",
            "gross profit", "gross margin", "net margin", "operating margin", "earnings quality"
        ],
        "revenue": [
            "annual revenue", "total sales", "net sales", "gross sales", "commercial revenue",
            "D2C revenue", "B2B revenue", "channel revenue", "top-line growth"
        ],
        "cost": [
            "COGS", "cost of goods sold", "operating expenses", "raw material cost", "procurement expense",
            "personnel expenses", "marketing expenditure", "distribution costs"
        ],
        "working_capital": [
            "inventory days", "receivable days", "payable days", "cash conversion cycle",
            "working capital cycle", "cash credit utilisation", "inventory turnover", "debtors"
        ],
        "sales_distribution": [
            "sales volume", "general trade", "modern trade", "e-commerce", "D2C website",
            "regional distribution", "outlet productivity", "b2b accounts", "order value"
        ],
        "customer_voc": [
            "customer retention", "cohort performance", "repeat purchase", "churn rate",
            "nps", "voice of customer", "support tickets", "account fit score", "acv"
        ],
        "operations_supply": [
            "inventory supply", "production capacity", "fulfilment rate", "on-time delivery",
            "supplier sla", "quality defect rate", "vendor scorecard", "lead time"
        ],
        "strategy_governance": [
            "corporate strategy", "leadership objectives", "competitive positioning", "market share",
            "growth strategy", "risk factors", "strategic priorities"
        ]
    }

    def expand(self, query: str, instruction_terms: Optional[List[str]] = None) -> ConceptExpansion:
        """Parses query and expands terms using taxonomy and instruction guidance."""
        q_lower = query.lower()
        matched_domains: Set[str] = set()
        primary_concepts: Set[str] = set()
        expanded_terms: Set[str] = set()
        generated_subqueries: List[str] = []

        # 1. Match query against concept taxonomy
        for domain, terms in self.CONCEPT_TAXONOMY.items():
            for t in terms:
                if t.lower() in q_lower or (len(t) > 3 and re.search(r"\b" + re.escape(t.lower()) + r"\b", q_lower)):
                    matched_domains.add(domain)
                    primary_concepts.add(t)
                    expanded_terms.update(terms)
                    break

        # Fallback keyword checks if no domain matched
        if not matched_domains:
            if any(w in q_lower for w in ["profit", "margin", "ebitda", "ebit", "loss"]):
                matched_domains.add("profitability")
                expanded_terms.update(self.CONCEPT_TAXONOMY["profitability"])
            if any(w in q_lower for w in ["revenue", "sale", "turnover", "top-line", "income"]):
                matched_domains.add("revenue")
                expanded_terms.update(self.CONCEPT_TAXONOMY["revenue"])
            if any(w in q_lower for w in ["working capital", "inventory", "receivable", "credit", "payable"]):
                matched_domains.add("working_capital")
                expanded_terms.update(self.CONCEPT_TAXONOMY["working_capital"])
            if any(w in q_lower for w in ["vendor", "supplier", "delivery", "quality"]):
                matched_domains.add("operations_supply")
                expanded_terms.update(self.CONCEPT_TAXONOMY["operations_supply"])
            if any(w in q_lower for w in ["customer", "cohort", "retention", "nps", "voc"]):
                matched_domains.add("customer_voc")
                expanded_terms.update(self.CONCEPT_TAXONOMY["customer_voc"])

        # Incorporate instruction terms if provided
        if instruction_terms:
            for term in instruction_terms:
                expanded_terms.add(term.lower())

        # Build dynamic, semantically rich subqueries from expanded concepts
        if "profitability" in matched_domains or "revenue" in matched_domains:
            generated_subqueries.extend([
                "annual revenue gross profit EBITDA net profit operating margin financial statement",
                "income statement EBIT EBITDA PAT gross margin historical revenue net profit",
                "DS08 Finance Commercial Economics revenue gross margin net profit",
            ])
        if "working_capital" in matched_domains:
            generated_subqueries.extend([
                "working capital cycle inventory days receivable days payable days cash credit",
                "DS08 Financial Working Capital inventory turnover cash conversion",
            ])
        if "sales_distribution" in matched_domains:
            generated_subqueries.extend([
                "sales volume regional breakdown general trade modern trade e-commerce revenue",
                "DS01 Consumer Sales Transactions order value product performance",
            ])
        if "customer_voc" in matched_domains:
            generated_subqueries.extend([
                "customer cohort performance retention churn voice of customer NPS",
                "DS04 Customer Cohort Performance DS09 Customer Experience VoC",
            ])
        if "operations_supply" in matched_domains:
            generated_subqueries.extend([
                "vendor performance evaluation scorecard delivery quality SLA compliance",
                "DS07 Operations Inventory Supply fulfilment defect rate",
            ])

        return ConceptExpansion(
            primary_concepts=sorted(list(primary_concepts)),
            expanded_terms=sorted(list(expanded_terms)),
            generated_subqueries=list(dict.fromkeys(generated_subqueries)),
        )
