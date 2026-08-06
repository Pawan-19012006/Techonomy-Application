"""Terminal Test Script for Phase 2 Knowledge Structuring Engine.

Pipeline Flow:
Parser -> Cleaner -> Structure Analyzer -> Hierarchy Builder -> Metadata Builder -> Statistics Generator
"""

from pathlib import Path
import sys
import fitz  # PyMuPDF

# Add project root directory to python path for standalone script execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.knowledge.ingestion.ingest import structure_pdf
from app.utils.logging import logger


def generate_structured_sample_pdf(output_path: Path) -> Path:
    """Generates a rich sample PDF containing headings, lists, tables, and paragraphs for structure testing.

    Args:
        output_path (Path): Target file path.

    Returns:
        Path: Path to generated PDF.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()

    # Page 1: Headings, Executive Summary, Bullet List
    page1 = doc.new_page()
    text1 = (
        "Techonomy Enterprise Knowledge Intelligence Platform\n"
        "Confidential Corporate Report 2026\n\n"
        "Section 1: Executive Summary\n\n"
        "Techonomy is building an enterprise-grade Knowledge Intelligence Platform powered by high-speed "
        "Retrieval-Augmented Generation (RAG) and modular backend pipelines.\n\n"
        "1.1 Key Achievements\n\n"
        "- Operational efficiency increased by 20% across all business units.\n"
        "- Processed over 1,200 enterprise PDF documents with sub-500ms latency.\n"
        "- Implemented zero-trust role-based access control.\n\n"
        "Confidential Corporate Report 2026\n"
    )
    page1.insert_text((50, 50), text1, fontsize=11)

    # Page 2: Subsections, Tables
    page2 = doc.new_page()
    text2 = (
        "Techonomy Enterprise Knowledge Intelligence Platform\n"
        "Section 2: Financial Performance\n\n"
        "The following table details quarterly revenue growth across enterprise segments:\n\n"
        "Quarter | Revenue ($M) | Growth (%)\n"
        "Q1 2026 | $12.4M       | +15%\n"
        "Q2 2026 | $14.8M       | +19%\n"
        "Q3 2026 | $18.2M       | +23%\n\n"
        "Overall revenue growth exceeded initial corporate targets by 4.2%.\n\n"
        "Confidential Corporate Report 2026\n"
    )
    page2.insert_text((50, 50), text2, fontsize=11)

    doc.save(str(output_path))
    doc.close()
    logger.info(f"Generated structured sample PDF at '{output_path}'.")
    return output_path


def print_hierarchy_node(section, depth=0):
    """Recursively prints a section hierarchy node."""
    indent = "  " * depth
    level_tag = f"H{section.level}" if section.section_type == "heading" else section.section_type.upper()
    print(f"{indent}└─ [{level_tag}] {section.title} (Page {section.page_number}, {section.char_count} chars)")


def main():
    """Main CLI execution routine for Phase 2 testing."""
    print("\n" + "=" * 70)
    print(" 🚀 TECHONOMY KNOWLEDGE STRUCTURING ENGINE - PHASE 2 TEST")
    print("=" * 70 + "\n")

    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
    else:
        sample_path = PROJECT_ROOT / "data" / "documents" / "structured_sample.pdf"
        if not sample_path.exists():
            generate_structured_sample_pdf(sample_path)
        pdf_path = sample_path

    print(f"📄 Target PDF File: {pdf_path}\n")

    try:
        # Run full Phase 1 + Phase 2 structuring pipeline
        structured_doc = structure_pdf(pdf_path)

        # Output Results
        print("=" * 70)
        print(" 📊 DOCUMENT STATISTICS SUMMARY")
        print("=" * 70)
        stats = structured_doc.statistics
        print(f" • Document ID:            {structured_doc.id}")
        print(f" • Filename:               {structured_doc.filename}")
        print(f" • Title:                  {structured_doc.title}")
        print(f" • Total Pages:            {stats.total_pages}")
        print(f" • Total Sections:         {stats.total_sections}")
        print(f" • Total Headings:         {stats.total_headings}")
        print(f" • Total Paragraphs:       {stats.total_paragraphs}")
        print(f" • Total Lists:            {stats.total_lists}")
        print(f" • Total Tables:           {stats.total_tables}")
        print(f" • Total Characters:       {stats.total_characters}")
        print(f" • Avg Section Length:     {stats.average_section_length} chars")
        print("-" * 70)

        # Print Detected Headings
        print("\n 📌 DETECTED HEADINGS:")
        headings = [sec for sec in structured_doc.sections if sec.section_type == "heading"]
        if headings:
            for h in headings:
                print(f"   [H{h.level}] Page {h.page_number} (Order #{h.reading_order}): \"{h.title}\"")
        else:
            print("   (No explicit headings detected)")

        # Print Detected Lists
        print("\n 📋 DETECTED LISTS:")
        lists = [sec for sec in structured_doc.sections if sec.section_type == "list"]
        if lists:
            for l in lists:
                preview = l.content.replace("\n", " ")[:80]
                print(f"   - Page {l.page_number} (Order #{l.reading_order}): \"{preview}...\"")
        else:
            print("   (No list structures detected)")

        # Print Detected Tables
        print("\n 📉 DETECTED TABLES:")
        tables = [sec for sec in structured_doc.sections if sec.section_type == "table"]
        if tables:
            for t in tables:
                preview = t.content.replace("\n", " ")[:80]
                print(f"   - Page {t.page_number} (Order #{t.reading_order}): \"{preview}...\"")
        else:
            print("   (No table structures detected)")

        # Print Flat Section Reading Order
        print("\n" + "-" * 70)
        print(" 📖 READING ORDER & SECTION METADATA SUMMARY:")
        print("-" * 70)
        for sec in structured_doc.sections:
            parent_info = f" -> Parent: #{sec.parent_id[:8]}" if sec.parent_id else " -> Root"
            print(
                f" #{sec.reading_order:02d} | Page {sec.page_number} | [{sec.section_type.upper():9s}] | "
                f"Level {sec.level} | {sec.char_count:4d} chars | Title: \"{sec.title[:35]}\"{parent_info}"
            )

        # Print Hierarchy Tree
        print("\n" + "-" * 70)
        print(" 🌳 DOCUMENT HIERARCHY TREE:")
        print("-" * 70)
        if structured_doc.hierarchy:
            for root in structured_doc.hierarchy:
                print_hierarchy_node(root, depth=0)
                children = [s for s in structured_doc.sections if s.parent_id == root.id]
                for child in children:
                    print_hierarchy_node(child, depth=1)
                    grand_children = [s for s in structured_doc.sections if s.parent_id == child.id]
                    for gchild in grand_children:
                        print_hierarchy_node(gchild, depth=2)
        else:
            print("   (No root hierarchy tree built)")

        print("\n" + "=" * 70)
        print(" ✅ PHASE 2 STRUCTURING PIPELINE TEST PASSED SUCCESSFULLY!")
        print("=" * 70 + "\n")

    except Exception as e:
        print("\n" + "=" * 70)
        print(f" ❌ PIPELINE TEST FAILED: {e}")
        print("=" * 70 + "\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
