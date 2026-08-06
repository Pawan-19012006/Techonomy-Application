"""Terminal Test Script for Phase 5 Knowledge Retrieval Engine.

Pipeline Flow:
User Query -> Query Processor -> Query Embedder -> Vector Search -> Reranker -> Context Builder -> RetrievalResult
"""

from pathlib import Path
import sys

# Add project root directory to python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.knowledge.indexing.qdrant_client import QdrantClientWrapper
from app.knowledge.ingestion.ingest import index_pdf
from app.knowledge.retrieval.retrieval_pipeline import RetrievalPipeline
from scripts.test_structure import generate_structured_sample_pdf


def ensure_knowledge_indexed() -> str:
    """Ensures Qdrant has indexed points available for testing.

    Returns:
        str: Target document filename.
    """
    client_wrapper = QdrantClientWrapper()
    count = client_wrapper.count_vectors(settings.QDRANT_COLLECTION_NAME)

    if count > 0:
        print(f"✅ Found {count} indexed vectors in Qdrant collection '{settings.QDRANT_COLLECTION_NAME}'.")
        return "annual_report.pdf"

    # Index sample document if Qdrant is empty
    sample_path = PROJECT_ROOT / "data" / "documents" / "annual_report.pdf"
    if not sample_path.exists():
        sample_path = PROJECT_ROOT / "data" / "documents" / "structured_sample.pdf"
        if not sample_path.exists():
            generate_structured_sample_pdf(sample_path)

    print(f"⚡ Indexing PDF '{sample_path.name}' into vector collection...")
    res = index_pdf(sample_path, recreate_collection=True)
    print(f"✅ Successfully indexed {res.vectors_uploaded} vectors from '{sample_path.name}'.")
    return sample_path.name


def print_retrieval_format(result, query_idx: int = 1):
    """Prints retrieval output matching the exact challenge specification format."""
    pq = result.processed_query
    context = result.context_package

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

    print("\n" + "=" * 52)
    print("SUCCESS")
    print("=" * 52 + "\n")


def main():
    """Main CLI execution routine for Phase 5 Knowledge Retrieval Engine testing."""

    print("\n" + "=" * 80)
    print("🚀 TECHONOMY KNOWLEDGE RETRIEVAL ENGINE - INTERACTIVE TEST")
    print("=" * 80 + "\n")

    # Ensure vectors exist
    ensure_knowledge_indexed()

    # Create retrieval pipeline
    pipeline = RetrievalPipeline()

    while True:
        question = input("\nAsk a question (type 'exit' to quit): ").strip()

        if question.lower() == "exit":
            print("\nGoodbye!\n")
            break

        if not question:
            continue

        try:
            result = pipeline.retrieve(
                query=question,
                top_k=10,
                top_n=5,
            )

            print_retrieval_format(result)

        except Exception as e:
            print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    main()
