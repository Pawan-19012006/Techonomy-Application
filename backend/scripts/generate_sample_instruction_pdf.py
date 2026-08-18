"""Generates sample analytical instruction PDFs using PyMuPDF (fitz) in backend/data/documents/instructions."""

import sys
from pathlib import Path
import fitz  # PyMuPDF

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.knowledge.ingestion.ingest import ingest_instruction_pdf
from app.utils.logging import logger


FINANCIAL_ANALYSIS_GUIDE_TEXT = """
FINANCIAL PERFORMANCE & MARGIN ANALYSIS INSTRUCTION GUIDE

Section 1: Financial Performance Metrics Framework
When analyzing company financial statements, annual reports, or quarterly performance disclosures:
1. Revenue & Sales Growth:
   - Identify revenue for the current reporting period and the previous comparison period.
   - Calculate Year-Over-Year (YoY) Revenue Growth Rate using the formula:
     YoY Growth (%) = ((Current Period Revenue - Prior Period Revenue) / Prior Period Revenue) * 100
   - Look for underlying drivers such as price increases, volume expansion, or new market entry.

2. Profitability Metrics & Margins:
   - Gross Profit = Revenue - Cost of Goods Sold (COGS)
   - Gross Margin (%) = (Gross Profit / Revenue) * 100
   - Operating Income (EBITDA) = Gross Profit - Operating Expenses (OPEX: R&D, Sales & Marketing, General & Administrative)
   - Operating Margin (%) = (Operating Income / Revenue) * 100
   - Net Profit = Operating Income - Taxes - Interest - Depreciation & Amortization
   - Net Profit Margin (%) = (Net Profit / Revenue) * 100

3. Cost Structure Analysis:
   - If net profit or operating margin declines despite revenue growth, check for inflationary pressure in COGS or sudden spikes in Sales & Marketing / Administrative expenses.
   - Analyze fixed vs variable cost structure changes between reporting periods.

Section 2: Document Search Strategy
- Target documents: Financial Statement.pdf, Annual Report.pdf, Balance Sheet.pdf, Income Statement.pdf.
- Search terms: "revenue", "gross profit", "operating expenses", "COGS", "EBITDA", "net income", "fiscal year", "quarterly growth".
"""

VENDOR_EVALUATION_GUIDE_TEXT = """
VENDOR PERFORMANCE & PROCUREMENT EVALUATION INSTRUCTION GUIDE

Section 1: Vendor Assessment Framework
When evaluating vendor performance, supplier scorecards, or procurement review reports:
1. On-Time Delivery Performance (OTD):
   - Measure actual delivery timestamps against agreed purchase order dates.
   - Target benchmark: > 95% on-time delivery.

2. Quality Score & Defect Rates:
   - Measure defect rate per 10,000 units delivered or acceptance percentage during receiving inspection.
   - Quality Score (%) = (Accepted Units / Total Delivered Units) * 100.

3. Pricing Competitiveness & Cost Variance:
   - Compare unit pricing against baseline contract prices and market indices.

4. Contract Compliance & Documentation:
   - Verify compliance with SLA requirements, safety certifications, and documentation completeness.

Section 2: Document Search Strategy
- Target documents: Vendor Performance Evaluation.pdf, Supplier Scorecard.pdf, Procurement Audit.pdf.
- Search terms: "on-time delivery", "quality score", "defect rate", "unit price", "SLA compliance", "vendor rating".
"""

SALES_PERFORMANCE_GUIDE_TEXT = """
SALES PERFORMANCE & REGIONAL ANALYSIS INSTRUCTION GUIDE

Section 1: Sales Analysis Framework
When analyzing sales volume, regional distribution, or customer segment performance:
1. Volume vs Value Analysis:
   - Distinguish total units sold from gross dollar revenue generated.
2. Regional & Geographic Segments:
   - Compare regional growth across North America, Europe, Asia Pacific, and emerging markets.
3. Customer Cohort Performance:
   - Evaluate enterprise accounts vs SMB customer segments.

Section 2: Document Search Strategy
- Target documents: Sales Performance Report.pdf, Regional Sales Summary.pdf, Commercial Report.pdf.
- Search terms: "sales volume", "units sold", "regional breakdown", "customer segment", "product category".
"""


def create_pdf_from_text(output_path: Path, title: str, text: str):
    doc = fitz.open()
    page = doc.new_page()
    
    # Title
    rect = fitz.Rect(50, 50, 550, 90)
    page.insert_textbox(rect, title, fontsize=16, fontname="helv", color=(0, 0.2, 0.6))
    
    # Body text
    body_rect = fitz.Rect(50, 100, 550, 750)
    page.insert_textbox(body_rect, text.strip(), fontsize=10, fontname="helv", color=(0.1, 0.1, 0.1))
    
    doc.save(str(output_path))
    doc.close()
    logger.info(f"Generated instruction PDF: {output_path.name}")


def main():
    target_dir = settings.BASE_DIR / "data" / "documents" / "instructions"
    target_dir.mkdir(parents=True, exist_ok=True)

    fin_path = target_dir / "financial_analysis_instruction.pdf"
    ven_path = target_dir / "vendor_evaluation_instruction.pdf"
    sal_path = target_dir / "sales_performance_instruction.pdf"

    create_pdf_from_text(fin_path, "Financial Performance & Margin Analysis Guide", FINANCIAL_ANALYSIS_GUIDE_TEXT)
    create_pdf_from_text(ven_path, "Vendor Evaluation & Procurement Scorecard Guide", VENDOR_EVALUATION_GUIDE_TEXT)
    create_pdf_from_text(sal_path, "Sales Performance & Regional Analysis Guide", SALES_PERFORMANCE_GUIDE_TEXT)

    # Ingest instruction PDFs into instruction_knowledge
    logger.info("=== Ingesting Analytical Instruction PDFs into 'instruction_knowledge' collection ===")
    ingest_instruction_pdf(fin_path)
    ingest_instruction_pdf(ven_path)
    ingest_instruction_pdf(sal_path)
    logger.info("✅ All sample instruction PDFs generated and indexed into Qdrant 'instruction_knowledge'!")


if __name__ == "__main__":
    main()
