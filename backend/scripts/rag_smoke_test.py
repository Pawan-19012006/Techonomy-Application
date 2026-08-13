"""CLI Test script for RAG Serving Pipeline (Phase 6).

Pipeline Flow:
User Question -> RetrievalPipeline -> PromptBuilder -> LLMService -> ChatResponse
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
from app.knowledge.rag.chat_service import ChatService
from app.knowledge.rag.llm_service import LLMService
from app.knowledge.rag.prompt_builder import PromptBuilder
from app.knowledge.models.search_result import SearchResult


def ensure_knowledge_base():
    """Ensures Qdrant collection is populated with annual_report.pdf vectors."""
    client_wrapper = QdrantClientWrapper()
    count = client_wrapper.count_vectors(settings.QDRANT_COLLECTION_NAME)
    docs = client_wrapper.get_indexed_documents(settings.QDRANT_COLLECTION_NAME)

    if count == 0 or "annual_report.pdf" not in docs:
        pdf_path = PROJECT_ROOT / "data" / "documents" / "annual_report.pdf"
        if pdf_path.exists():
            print(f"⚡ Indexing '{pdf_path.name}' into Qdrant vector database...")
            res = index_pdf(pdf_path, recreate_collection=True)
            print(f"✅ Indexed {res.vectors_uploaded} vectors into '{settings.QDRANT_COLLECTION_NAME}'.")
        else:
            print("⚠️ Warning: 'annual_report.pdf' not found for indexing.")


def test_prompt_builder():
    """Validates PromptBuilder prompt formatting."""
    print("\n" + "=" * 80)
    print(" 🛠️ TESTING PROMPT BUILDER")
    print("=" * 80)

    builder = PromptBuilder()
    sample_chunks = [
        SearchResult(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_name="annual_report.pdf",
            score=0.85,
            content="Total Revenue from operations for FY24 stood at INR 4,520 Crores.",
            page_numbers=[45],
            section_title="FINANCIAL PERFORMANCE",
        ),
        SearchResult(
            chunk_id="chunk-2",
            document_id="doc-1",
            document_name="annual_report.pdf",
            score=0.78,
            content="EBITDA margin improved by 150 bps year-on-year.",
            page_numbers=[46],
            section_title="OPERATIONAL REVIEW",
        ),
    ]

    prompt = builder.build_prompt("What was the total revenue?", sample_chunks)
    print(prompt)
    print("=" * 80 + "\n")
    return prompt


def test_chat_service(question: str = "What is the company's revenue?"):
    """Validates ChatService execution end-to-end."""
    print("\n" + "=" * 80)
    print(" 🚀 TESTING CHAT SERVICE RAG PIPELINE")
    print("=" * 80)
    print(f"Question: '{question}'\n")

    ensure_knowledge_base()

    # Instantiate ChatService
    chat_service = ChatService()

    try:
        result = chat_service.ask(query=question, top_k=10, top_n=5)
        print("Answer:")
        print(result.answer)
        print("\nSources:")
        for src in result.sources:
            print(f" • Document: {src.document} | Page: {src.page}")
        print(f"\nConfidence: {result.confidence}")
    except Exception as e:
        print(f"⚠️ OpenRouter / ChatService notice: {e}")
        print("(Note: If OPENROUTER_API_KEY is not set in .env, OpenRouterAPIError is expected)")

    print("=" * 80 + "\n")


def main():
    print("\n" + "=" * 80)
    print(" 🎯 TECHONOMY RAG SERVING PIPELINE TEST")
    print("=" * 80)

    test_prompt_builder()
    test_chat_service("What is the company's revenue?")


if __name__ == "__main__":
    main()
