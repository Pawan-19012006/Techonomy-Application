"""Terminal Test Script for Phase 1 Ingestion Pipeline (PDF -> Parser -> Cleaner -> Document)."""

from pathlib import Path
import sys
import fitz  # PyMuPDF to generate sample PDF if needed

# Add project root directory to python path for standalone script execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.knowledge.ingestion.ingest import ingest_pdf
from app.utils.logging import logger


def generate_sample_pdf(output_path: Path) -> Path:
    """Generates a sample 3-page PDF document for standalone terminal testing.

    Args:
        output_path (Path): Target file path.

    Returns:
        Path: Path to generated PDF.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()

    # Page 1
    page1 = doc.new_page()
    text1 = (
        "Techonomy Enterprise Knowledge Intelligence Platform\n"
        "Confidential Corporate Report 2026\n\n"
        "Section 1: Executive Summary\n"
        "Techonomy is building an enterprise-grade Knowledge Intelligence Platform powered by high-speed "
        "Retrieval-Augmented Generation (RAG) and modular backend pipelines.   This document outlines "
        "the architecture and   performance metrics for Q3 2026.\n\n"
        "Key highlights include a 20% increase in operational efficiency and seamless API integrations.\n"
        "Confidential Corporate Report 2026\n"
    )
    page1.insert_text((50, 50), text1, fontsize=11)

    # Page 2
    page2 = doc.new_page()
    text2 = (
        "Techonomy Enterprise Knowledge Intelligence Platform\n"
        "Section 2: Financial Performance & Market Growth\n\n"
        "In Q3 2026, Techonomy expanded enterprise client onboarding by 35%.   Revenue growth was strongest "
        "in North America and South India regions.   The company maintained a 99.9% API uptime across all endpoints.\n\n"
        "Total processed documents reached over 1,200 PDF files with an average response latency under 450ms.\n"
        "Confidential Corporate Report 2026\n"
    )
    page2.insert_text((50, 50), text2, fontsize=11)

    # Page 3
    page3 = doc.new_page()
    text3 = (
        "Techonomy Enterprise Knowledge Intelligence Platform\n"
        "Section 3: Security & Governance Guidelines\n\n"
        "All customer data is encrypted in transit using TLS 1.3 and at rest using AES-256 encryption.   "
        "Role-based access control (RBAC) ensures strict tenant separation between enterprise teams.\n\n"
        "For security inquiries, contact security@techonomy.com.\n"
        "Confidential Corporate Report 2026\n"
    )
    page3.insert_text((50, 50), text3, fontsize=11)

    doc.save(str(output_path))
    doc.close()
    logger.info(f"Generated sample 3-page test PDF at '{output_path}'.")
    return output_path


def main():
    """Main CLI execution routine."""
    print("\n" + "=" * 60)
    print(" 🚀 TECHONOMY KNOWLEDGE ENGINE - PHASE 1 PIPELINE TEST")
    print("=" * 60 + "\n")

    # Determine input PDF path
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
    else:
        sample_path = PROJECT_ROOT / "data" / "documents" / "sample_report.pdf"
        if not sample_path.exists():
            generate_sample_pdf(sample_path)
        pdf_path = sample_path

    print(f"📄 Processing target PDF: {pdf_path}\n")

    try:
        # Run Ingestion Pipeline (PDF -> Parser -> Cleaner -> Clean Document)
        clean_doc = ingest_pdf(pdf_path)

        # Output Results
        print("=" * 60)
        print(" 📊 INGESTION RESULT SUMMARY")
        print("=" * 60)
        print(f" • Document ID:     {clean_doc.id}")
        print(f" • Filename:        {clean_doc.filename}")
        print(f" • Title:           {clean_doc.title}")
        print(f" • File Type:       {clean_doc.file_type}")
        print(f" • Total Pages:     {clean_doc.total_pages}")
        print(f" • Total Chars:     {clean_doc.total_characters}")
        print("-" * 60)

        print("\n 📄 PAGE CHARACTER COUNTS:")
        for page in clean_doc.pages:
            print(f"   - Page {page.page_number}: {page.char_count} characters")

        print("\n" + "-" * 60)
        print(" 🔍 PREVIEW - FIRST PAGE (Page 1):")
        print("-" * 60)
        first_page_text = clean_doc.pages[0].text if clean_doc.pages else "[Empty]"
        preview_first = first_page_text[:300] + ("..." if len(first_page_text) > 300 else "")
        print(preview_first)

        print("\n" + "-" * 60)
        print(f" 🔍 PREVIEW - LAST PAGE (Page {clean_doc.total_pages}):")
        print("-" * 60)
        last_page_text = clean_doc.pages[-1].text if clean_doc.pages else "[Empty]"
        preview_last = last_page_text[:300] + ("..." if len(last_page_text) > 300 else "")
        print(preview_last)

        print("\n" + "=" * 60)
        print(" ✅ PHASE 1 PIPELINE TEST PASSED SUCCESSFULLY!")
        print("=" * 60 + "\n")

    except Exception as e:
        print("\n" + "=" * 60)
        print(f" ❌ PIPELINE TEST FAILED: {e}")
        print("=" * 60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
