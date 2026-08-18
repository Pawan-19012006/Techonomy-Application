"""Temporal Resolution Layer for resolving relative and explicit time expressions in company RAG queries."""

import re
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class TemporalResolution(BaseModel):
    """Structure representing resolved temporal references for a query."""

    original_reference: Optional[str] = Field(default=None, description="Extracted time expression from query")
    resolved_periods: List[str] = Field(default_factory=list, description="Resolved fiscal years or reporting periods")
    comparison_type: Optional[str] = Field(default=None, description="Type of comparison (yoy, mom, multi_year, period_over_period)")
    temporal_search_terms: List[str] = Field(default_factory=list, description="Generated temporal search terms for vector query")


class TemporalResolver:
    """Resolves relative temporal expressions against known company document reporting period standards."""

    # Grounded reporting period anchors established in official company documents
    # Company reporting span: FY 2021-22 through FY 2025-26, 9M FY25 / 9M FY26, monthly cohort data up to Mar-2026.
    DEFAULT_FISCAL_YEARS = ["FY 2021-22", "FY 2022-23", "FY 2023-24", "FY 2024-25", "FY 2025-26"]
    LATEST_FULL_FY = "FY 2025-26"
    PREVIOUS_FULL_FY = "FY 2024-25"
    LATEST_PERIOD_LABEL = "9M FY26"
    PREVIOUS_PERIOD_LABEL = "9M FY25"

    def __init__(self):
        pass

    def resolve(self, query: str) -> TemporalResolution:
        """Parses query text and resolves temporal references to company dataset reporting periods."""
        q_lower = query.lower()

        extracted_ref: Optional[str] = None
        resolved_periods: List[str] = []
        comparison_type: Optional[str] = None
        search_terms: List[str] = []

        # 1. Check relative year patterns ("last year", "previous year", "this year", "latest year")
        if re.search(r"\b(last year|previous year|prior year|past year)\b", q_lower):
            extracted_ref = "last year"
            resolved_periods = [self.PREVIOUS_FULL_FY]
            search_terms.extend([self.PREVIOUS_FULL_FY, "FY 2024-25", "FY 2024–25", "FY25", "prior year financial"])
        elif re.search(r"\b(this year|latest year|current year|current period|recent year)\b", q_lower):
            extracted_ref = "latest year"
            resolved_periods = [self.LATEST_FULL_FY]
            search_terms.extend([self.LATEST_FULL_FY, "FY 2025-26", "FY 2025–26", "FY26", "latest financial year"])
        elif re.search(r"\b(all available financial years|across all years|historical|5-year|five-year|multi-year)\b", q_lower):
            extracted_ref = "all available financial years"
            resolved_periods = self.DEFAULT_FISCAL_YEARS
            comparison_type = "multi_year"
            search_terms.extend([
                "FY 2021-22 FY 2022-23 FY 2023-24 FY 2024-25 FY 2025-26",
                "five-year revenue net profit history financial year",
                "historical financial performance across reporting periods",
            ])

        # 2. Check month patterns ("last month", "latest month", "previous month", "monthly")
        elif re.search(r"\b(last month|latest month|previous month|recent month|monthly revenue|monthly sales)\b", q_lower):
            extracted_ref = "last month"
            resolved_periods = ["Dec-2025", "Mar-2026", "9M FY26"]
            comparison_type = "mom"
            search_terms.extend([
                "monthly consumer sales transaction analytics revenue",
                "DS01 Consumer Sales Transaction monthly revenue",
                "DS04 Customer Cohort Performance monthly revenue retention",
                "monthly performance reporting period sales",
            ])

        # 3. Check quarter / 9M period patterns ("latest quarter", "previous quarter", "9 months", "9m")
        elif re.search(r"\b(latest quarter|recent quarter|9 months|nine months|9m|q4|q3|q2|q1)\b", q_lower):
            extracted_ref = "nine months / quarter"
            resolved_periods = [self.LATEST_PERIOD_LABEL, self.PREVIOUS_PERIOD_LABEL]
            comparison_type = "period_over_period"
            search_terms.extend([
                "nine months ended 31 December 9M FY26 9M FY25",
                "quarterly revenue gross profit EBIT EBIT margin",
                "Q4 FY25 Q4 L full year budgeted revenue",
            ])

        # 4. Check explicit YoY / comparison patterns ("year over year", "yoy", "compare", "reporting periods")
        if any(w in q_lower for w in ["yoy", "year-over-year", "year over year", "growth", "change", "compared", "reporting period"]):
            if not comparison_type:
                comparison_type = "yoy"
            search_terms.extend([
                "period comparison financial statement YoY growth percentage",
                "revenue net profit margin growth across reporting periods",
            ])

        # If no explicit temporal phrase was extracted, add default company period search terms
        if not search_terms:
            search_terms = ["reporting period financial year FY25 FY26 revenue profit"]

        return TemporalResolution(
            original_reference=extracted_ref,
            resolved_periods=list(dict.fromkeys(resolved_periods)),
            comparison_type=comparison_type,
            temporal_search_terms=list(dict.fromkeys(search_terms)),
        )
