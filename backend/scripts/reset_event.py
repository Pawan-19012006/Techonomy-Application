"""Event Knowledge Base Reset and Ingestion Script.

Wipes old knowledge from Qdrant Cloud/Local and re-indexes new event PDFs from data/documents/.
"""

import os
from pathlib import Path
import sys
from typing import Optional

# Ensure backend root is on sys.path for standalone script execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.knowledge.indexing.collection_manager import CollectionManager
from app.knowledge.indexing.embedder import EmbeddingGenerator
from app.knowledge.indexing.index_manager import IndexManager
from app.knowledge.indexing.qdrant_client import QdrantClientWrapper
from app.knowledge.ingestion.ingest import IngestionPipeline
from app.utils.logging import logger


def discover_pdfs(documents_dir: Path) -> list[Path]:
    """Discovers all *.pdf files in the documents directory.

    Args:
        documents_dir (Path): Path to documents directory.

    Returns:
        list[Path]: Sorted list of PDF file paths.
    """
    if not documents_dir.exists():
        return []
    return sorted(list(documents_dir.glob("*.pdf")))


def reset_and_index_event(
    documents_dir: Optional[Path] = None,
    auto_confirm: bool = False,
    collection_name: str = settings.QDRANT_COLLECTION_NAME,
) -> bool:
    """Executes safe knowledge base reset and re-indexing workflow.

    Args:
        documents_dir (Optional[Path]): Directory containing event PDFs.
        auto_confirm (bool): If True, skips interactive confirmation prompt.
        collection_name (str): Qdrant target collection name.

    Returns:
        bool: True if reset and ingestion succeed cleanly.
    """
    target_dir = documents_dir or (PROJECT_ROOT / "data" / "documents")
    pdf_files = discover_pdfs(target_dir)

    # Safety Check 1: Must have at least 1 PDF
    if not pdf_files:
        rel_dir = target_dir.relative_to(PROJECT_ROOT) if target_dir.is_relative_to(PROJECT_ROOT) else target_dir
        print("\n" + "=" * 50)
        print(f"ERROR: No PDF files found in {rel_dir}/")
        print("Please place the event PDF files in that directory and run the command again.")
        print("=" * 50 + "\n")
        return False

    # Safety Check 2: Destructive Confirmation Prompt
    if not auto_confirm:
        print("\n" + "=" * 50)
        print("TECHONOMY KNOWLEDGE BASE RESET")
        print("=" * 50)
        print(f"\nThis operation will DELETE the existing Qdrant collection:\n\n{collection_name}\n")
        print("All currently indexed documents/chunks will be permanently removed.\n")
        print("PDF files found:")
        for idx, pdf in enumerate(pdf_files, start=1):
            print(f"  {idx}. {pdf.name}")
        print()

        try:
            user_input = input("Continue? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            user_input = "n"

        if user_input not in ("y", "yes"):
            print("\nReset operation aborted. No changes were made to Qdrant.\n")
            return False

    print(f"\n🚀 Initiating Knowledge Base Reset for collection '{collection_name}'...")

    try:
        # Step 1: Initialize Qdrant Client Wrapper & Collection Manager
        client_wrapper = QdrantClientWrapper()
        collection_mgr = CollectionManager(
            client_wrapper=client_wrapper,
            collection_name=collection_name,
        )

        # Step 2: Recreate Collection (Destructive Clean Reset)
        embedder = EmbeddingGenerator(model_name=settings.EMBEDDING_MODEL_NAME)
        dimension = embedder.get_dimension()

        print(f"⚙️ Recreating Qdrant collection '{collection_name}' (dim={dimension}, metric={settings.QDRANT_DISTANCE_METRIC})...")
        collection_mgr.ensure_collection(
            embedding_dimension=dimension,
            recreate=True,
        )
        print(f"   ✓ Collection '{collection_name}' recreated cleanly.")

        # Step 3: Ingest Discovered PDFs
        index_mgr = IndexManager(
            client_wrapper=client_wrapper,
            collection_name=collection_name,
        )
        pipeline = IngestionPipeline(index_manager=index_mgr)

        total_chunks = 0
        total_vectors = 0

        for idx, pdf_path in enumerate(pdf_files, start=1):
            print(f"\n📄 [{idx}/{len(pdf_files)}] Ingesting & Indexing '{pdf_path.name}'...")
            res = pipeline.process_pdf_to_index(
                file_path=pdf_path,
                document_id=None,
                max_tokens=512,
                recreate_collection=False,
                collection_name=collection_name,
            )
            total_chunks += res.chunks_indexed
            total_vectors += res.vectors_uploaded
            print(f"   ✓ Success: Indexed {res.chunks_indexed} chunks ({res.vectors_uploaded} vectors).")

        # Step 4: Final Verification Probe
        print("\n🔍 Running Post-Ingestion Verification Checks...")
        info = client_wrapper.collection_info(collection_name)
        vector_count = client_wrapper.count_vectors(collection_name)
        indexed_docs = client_wrapper.get_indexed_documents(collection_name)
        expected_doc_names = sorted([p.name for p in pdf_files])

        col_status = str(info.get("status", "")).lower()
        is_status_ok = col_status not in ("not_found", "unhealthy") and vector_count > 0

        # Verify all PDFs are present in payload document names
        missing_docs = set(expected_doc_names) - set(indexed_docs)
        unexpected_docs = set(indexed_docs) - set(expected_doc_names)

        if not is_status_ok:
            print(f"❌ Verification Failed: Collection status '{info.get('status')}', vector_count={vector_count}.")
            return False

        if missing_docs:
            print(f"❌ Verification Failed: Missing expected documents in collection: {sorted(list(missing_docs))}")
            return False

        if unexpected_docs:
            print(f"❌ Verification Failed: Found unexpected stale documents in collection: {sorted(list(unexpected_docs))}")
            return False

        # Step 5: Format Final Summary Output
        print("\n" + "=" * 50)
        print("KNOWLEDGE BASE READY")
        print("=" * 50)
        print(f"\nCollection:\n{collection_name}\n")
        print(f"Documents:\n{len(pdf_files)}\n")
        print("Indexed documents:")
        for doc_name in expected_doc_names:
            print(f"  ✓ {doc_name}")
        print(f"\nTotal vectors:\n{vector_count}\n")
        print("Status:\nREADY\n")
        print("=" * 50 + "\n")

        return True

    except Exception as e:
        logger.error(f"Event Knowledge Base Reset Failed: {e}", exc_info=True)
        print(f"\n❌ ERROR: Reset workflow failed: {e}\n")
        return False


def main():
    """Main CLI entrypoint."""
    args = sys.argv[1:]
    auto_confirm = "--yes" in args or "-y" in args or os.environ.get("AUTO_CONFIRM") == "1"

    success = reset_and_index_event(auto_confirm=auto_confirm)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
