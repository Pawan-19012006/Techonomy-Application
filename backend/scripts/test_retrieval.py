"""Terminal Test Script for Phase 5 Knowledge Retrieval Engine.

Pipeline Flow:
User Query -> Query Processor -> Query Embedder -> Vector Search -> Reranker -> Context Builder -> RetrievalResult
"""

from pathlib import Path
import sys

# Add project root directory to python path for standalone script execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.knowledge.indexing.qdrant_client import QdrantClientWrapper
from app.knowledge.ingestion.ingest import index_pdf
from app.knowledge.retrieval.retrieval_pipeline import RetrievalPipeline
from scripts.test_structure import generate_structured_sample_pdf


def ensure_knowledge_indexed() -> str:
    """Ensures Qdrant contains the indexed production annual_report.pdf.

    Returns:
        str: Target document filename.
    """
    client_wrapper = QdrantClientWrapper()
    col_name = settings.QDRANT_COLLECTION_NAME
    storage_path = Path(settings.QDRANT_STORAGE_PATH).resolve()

    count = client_wrapper.count_vectors(col_name)
    indexed_docs = client_wrapper.get_indexed_documents(col_name)

    # Check if annual_report.pdf is present in indexed_docs
    has_annual_report = "annual_report.pdf" in indexed_docs

    if count > 0 and has_annual_report:
        print("\n" + "=" * 80)
        print(" 🔍 QDRANT PERSISTENCE & AUDIT LOG")
        print("=" * 80)
        print(f" • Storage Path:          {storage_path}")
        print(f" • Collection Name:       {col_name}")
        print(f" • Total Vectors:         {count}")
        print(f" • Indexed Document Names: {', '.join(indexed_docs)}")
        print("=" * 80 + "\n")
        return "annual_report.pdf"

    # Index production annual_report.pdf if empty or missing
    prod_path = PROJECT_ROOT / "data" / "documents" / "annual_report.pdf"
    if not prod_path.exists():
        sample_path = PROJECT_ROOT / "data" / "documents" / "structured_sample.pdf"
        if not sample_path.exists():
            generate_structured_sample_pdf(sample_path)
        prod_path = sample_path

    print(f"⚡ Indexing production document '{prod_path.name}' into vector collection...")
    res = index_pdf(prod_path, recreate_collection=True)
    count = client_wrapper.count_vectors(col_name)
    indexed_docs = client_wrapper.get_indexed_documents(col_name)

    print("\n" + "=" * 80)
    print(" 🔍 QDRANT PERSISTENCE & AUDIT LOG")
    print("=" * 80)
    print(f" • Storage Path:          {storage_path}")
    print(f" • Collection Name:       {col_name}")
    print(f" • Total Vectors:         {count}")
    print(f" • Indexed Document Names: {', '.join(indexed_docs)}")
    print("=" * 80 + "\n")

    return prod_path.name


def print_retrieval_format(result):
    """Prints retrieval output matching the exact challenge specification format."""
    pq = result.processed_query
    context = result.context_package
    retrieved_docs = sorted(list({item.document_name for item in result.reranked_results}))

    print("\n" + "=" * 52)
    print("TECHONOMY RETRIEVAL ENGINE")
    print("=" * 52 + "\n")

    print("Query:")
    print(f'"{pq.original_query}"\n')

    print("Processed Query:")
    print(f'"{pq.normalized_query}"\n')

    print("Embedding Dimension:")
    print(f"{result.embedding_dimension}\n")

    print("Vector Search")
    print(f"Top {len(result.raw_search_results)} Retrieved")
    print("-" * 52)

    for rank, item in enumerate(result.raw_search_results, start=1):
        pages_str = ", ".join(str(p) for p in item.page_numbers) if item.page_numbers else "1"
        print(f"Rank {rank}")
        print(f"Score: {item.score:.2f}")
        print(f"Document:\n{item.document_name}")
        print(f"Page:\n{pages_str}")
        print(f"Section:\n{item.section_title}")
        print("-" * 52)

    print("\nAfter Reranking")
    print(f"Top {len(result.reranked_results)} Results")
    print("-" * 52)
    for rank, item in enumerate(result.reranked_results, start=1):
        pages_str = ", ".join(str(p) for p in item.page_numbers) if item.page_numbers else "1"
        print(f"Rank {rank} | Score: {item.score:.2f} | Doc: {item.document_name} | Page: {pages_str} | Section: {item.section_title}")

    print("\nContext Built")
    print("Estimated Tokens:")
    print(f"{context.estimated_tokens}\n")

    print("Sources")
    for src in context.sources:
        print(src)

    print("\nRetrieved Document Names:")
    print(", ".join(retrieved_docs))

    print("\n" + "=" * 52)
    print("SUCCESS")
    print("=" * 52 + "\n")


def main():
    """Main CLI execution routine for Phase 5 Knowledge Retrieval Engine testing."""
    print("\n" + "=" * 80)
    print(" 🚀 TECHONOMY KNOWLEDGE RETRIEVAL ENGINE - PHASE 5 TEST")
    print("=" * 80 + "\n")

    # Step 1: Ensure indexed document exists and log audit
    ensure_knowledge_indexed()

    pipeline = RetrievalPipeline()

    # Predefined test questions
    test_questions = [
        "What is the company's revenue?",
        "What are the major business segments?",
        "What risks were identified?",
        "Who is the Managing Director?",
    ]

    # Check command line flags
    if "--interactive" in sys.argv or "-i" in sys.argv:
        print("🎮 Entering Interactive Question Answering Mode (type 'exit' to quit)...")
        while True:
            question = input("\nAsk a question: ").strip()
            if question.lower() == "exit":
                print("\nGoodbye!\n")
                break
            if not question:
                continue
            try:
                res = pipeline.retrieve(query=question, top_k=10, top_n=5)
                print_retrieval_format(res)
            except Exception as e:
                print(f"\n❌ Error processing query: {e}\n")
    else:
        # If specific query passed via CLI
        cli_args = [a for a in sys.argv[1:] if not a.startswith("-")]
        if cli_args:
            test_questions = [" ".join(cli_args)]

        for question in test_questions:
            try:
                res = pipeline.retrieve(query=question, top_k=10, top_n=5)
                print_retrieval_format(res)
            except Exception as e:
                print(f"\n❌ Error processing query '{question}': {e}\n")


if __name__ == "__main__":
    main()
