"""Evidence Coverage Checker for assessing candidate evidence completeness and triggering targeted iterative retrieval."""

import re
from typing import List, Set
from pydantic import BaseModel, Field

from app.knowledge.models.search_result import SearchResult


class EvidenceCoverageReport(BaseModel):
    """Report detailing evidence coverage analysis and missing metric subqueries."""

    is_sufficient: bool = Field(default=True, description="Whether retrieved evidence covers query requirements")
    found_metrics: List[str] = Field(default_factory=list, description="Required metrics found in candidate evidence")
    missing_metrics: List[str] = Field(default_factory=list, description="Required metrics missing from candidate evidence")
    has_numerical_evidence: bool = Field(default=False, description="Whether evidence contains numerical values/tables")
    targeted_fallback_queries: List[str] = Field(default_factory=list, description="Targeted subqueries for missing evidence")


class EvidenceChecker:
    """Evaluates candidate SearchResult chunks against query requirements and constructs iterative retrieval queries."""

    METRIC_KEYWORDS = {
        "revenue": ["revenue", "sales", "turnover", "top-line", "d2c"],
        "net_profit": ["net profit", "pat", "profit after tax", "net income"],
        "gross_profit": ["gross profit", "gross margin", "cogs"],
        "ebitda": ["ebitda", "ebit", "operating profit", "operating margin"],
        "working_capital": ["working capital", "inventory days", "receivable days", "payable days", "cash credit"],
        "customer": ["retention", "cohort", "churn", "nps", "voc", "customer experience"],
        "vendor": ["vendor", "supplier", "scorecard", "delivery performance", "quality score"],
    }

    def check_coverage(self, candidates: List[SearchResult], required_metrics: List[str], intent: str) -> EvidenceCoverageReport:
        """Evaluates whether candidates contain required metric concepts and numerical tables."""
        if not candidates:
            return EvidenceCoverageReport(
                is_sufficient=False,
                missing_metrics=required_metrics,
                has_numerical_evidence=False,
                targeted_fallback_queries=self._build_fallback_queries(required_metrics, intent),
            )

        combined_text = "\n".join([c.content.lower() for c in candidates])
        found_metrics: Set[str] = set()
        missing_metrics: List[str] = []

        # 1. Check required metrics
        for metric in required_metrics:
            synonyms = self.METRIC_KEYWORDS.get(metric.lower(), [metric.lower()])
            if any(syn in combined_text for syn in synonyms):
                found_metrics.add(metric)
            else:
                missing_metrics.append(metric)

        # 2. Check presence of numerical figures / tabular data
        has_numbers = bool(re.search(r"\b\d+(?:\.\d+)?%?|\b(?:lakh|crore|thousand|million|fy2\d)\b", combined_text))

        # Determine overall sufficiency
        # Sufficient if at least 50% of required metrics are found and numerical data exists
        is_sufficient = (len(found_metrics) >= max(1, len(required_metrics) // 2)) and has_numbers

        fallback_queries = []
        if missing_metrics or not is_sufficient:
            fallback_queries = self._build_fallback_queries(missing_metrics or required_metrics, intent)

        return EvidenceCoverageReport(
            is_sufficient=is_sufficient,
            found_metrics=sorted(list(found_metrics)),
            missing_metrics=missing_metrics,
            has_numerical_evidence=has_numbers,
            targeted_fallback_queries=fallback_queries,
        )

    def _build_fallback_queries(self, missing_metrics: List[str], intent: str) -> List[str]:
        """Builds targeted fallback vector search queries for missing metrics."""
        queries: List[str] = []

        for m in missing_metrics:
            m_clean = m.replace("_", " ").lower()
            if "profit" in m_clean or "net" in m_clean or "revenue" in m_clean:
                queries.append(f"1.pdf 3.pdf financial statement {m_clean} history reporting period")
                queries.append(f"annual revenue net profit {m_clean} FY 2021-22 to FY 2025-26")
            elif "working" in m_clean or "inventory" in m_clean or "receivable" in m_clean:
                queries.append("DS08 Financial Commercial Economics inventory days receivable days working capital")
                queries.append("1.pdf 3.pdf working capital cycle cash credit utilisation")
            elif "customer" in m_clean or "retention" in m_clean:
                queries.append("DS04 Customer Cohort Performance DS09 Customer Experience retention churn NPS")
            elif "vendor" in m_clean or "supplier" in m_clean:
                queries.append("vendor evaluation scorecard delivery quality SLA contract compliance")
            else:
                queries.append(f"official company document {m_clean} evidence reporting period")

        return list(dict.fromkeys(queries))
