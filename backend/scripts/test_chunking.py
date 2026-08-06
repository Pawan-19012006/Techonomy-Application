"""Terminal Test Script for Phase 3 Knowledge Optimization Engine (Chunking).

Pipeline Flow:
Parser -> Cleaner -> Structure Analyzer -> Hierarchy Builder -> Metadata Builder -> Statistics Generator -> Semantic Chunker -> Chunk Optimizer -> Chunk Validator -> Token Estimator -> KnowledgeChunks
"""

from pathlib import Path
import sys

# Add project root directory to python path for standalone script execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.knowledge.ingestion.ingest import chunk_pdf
from scripts.test_structure import generate_structured_sample_pdf


def main():
    """Main CLI execution routine for Phase 3 testing."""
    print("\n" + "=" * 75)
    print(" 🚀 TECHONOMY KNOWLEDGE OPTIMIZATION ENGINE - PHASE 3 CHUNKING TEST")
    print("=" * 75 + "\n")

    # Determine input PDF path
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
    else:
        sample_path = PROJECT_ROOT / "data" / "documents" / "structured_sample.pdf"
        if not sample_path.exists():
            generate_structured_sample_pdf(sample_path)
        pdf_path = sample_path

    print(f"📄 Target PDF File: {pdf_path}\n")

    try:
        # Run full end-to-end pipeline (Phase 1 + 2 + 3)
        chunks, stats = chunk_pdf(pdf_path, max_tokens=512)

        # Output Results
        print("=" * 75)
        print(" 📊 CHUNK STATISTICS & VALIDATION SUMMARY")
        print("=" * 75)
        print(f" • Total Valid Chunks:       {stats.total_chunks}")
        print(f" • Average Chunk Size:       {stats.average_chunk_size} characters")
        print(f" • Largest Chunk Size:       {stats.largest_chunk} characters")
        print(f" • Smallest Chunk Size:      {stats.smallest_chunk} characters")
        print(f" • Average Estimated Tokens: {stats.average_tokens} tokens")
        print(f" • Aggregate Total Tokens:   {stats.total_tokens} tokens")
        print("-" * 75)

        # Print Chunk Details in Reading Order
        print("\n 📖 GENERATED KNOWLEDGE CHUNKS (IN READING ORDER):")
        print("-" * 75)
        for chunk in chunks:
            pages_str = ", ".join(str(p) for p in chunk.page_numbers)
            print(
                f" Chunk #{chunk.reading_order:02d} | ID: {chunk.chunk_id[:8]}... | "
                f"Pages: [{pages_str}] | Type: [{chunk.section_type.upper():9s}] | "
                f"Tokens: {chunk.estimated_tokens:3d} (~{chunk.char_count:4d} chars)"
            )
            print(f"   ├─ Governing Section: \"{chunk.section_title}\"")
            print(f"   ├─ Metadata: {chunk.metadata}")
            print("   └─ Content Preview:")
            preview = chunk.content.replace("\n", " ")
            if len(preview) > 140:
                preview = preview[:140] + "..."
            print(f"      \"{preview}\"\n")

        print("=" * 75)
        print(" ✅ PHASE 3 CHUNKING PIPELINE TEST PASSED SUCCESSFULLY!")
        print("=" * 75 + "\n")

    except Exception as e:
        print("\n" + "=" * 75)
        print(f" ❌ PIPELINE TEST FAILED: {e}")
        print("=" * 75 + "\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
