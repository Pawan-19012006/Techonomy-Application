"""Debug Utility for inspecting Qdrant storage path, collection details, total points, document names, and chunk IDs."""

from pathlib import Path
import sys

# Add project root directory to python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.knowledge.indexing.qdrant_client import QdrantClientWrapper


def debug_qdrant_storage(collection_name: str = settings.QDRANT_COLLECTION_NAME):
    """Inspects and prints Qdrant collection status, storage path, point count, document names, and chunk IDs."""
    client_wrapper = QdrantClientWrapper()
    storage_path = Path(settings.QDRANT_STORAGE_PATH).resolve()

    total_points = client_wrapper.count_vectors(collection_name)
    doc_names = client_wrapper.get_indexed_documents(collection_name)
    sample_points = client_wrapper.get_sample_points(collection_name, limit=10)

    print("\n" + "=" * 80)
    print(" 🛠️ TECHONOMY QDRANT VECTOR DATABASE DEBUG UTILITY")
    print("=" * 80)
    print(f" • Collection Name:         {collection_name}")
    print(f" • Storage Path:             {storage_path}")
    print(f" • Total Vector Points:     {total_points}")
    print("-" * 80)

    print("\n 📄 INDEXED DOCUMENTS IN COLLECTION:")
    if doc_names:
        for idx, name in enumerate(doc_names[:10], start=1):
            print(f"   [{idx:2d}] {name}")
        if len(doc_names) > 10:
            print(f"   ... and {len(doc_names) - 10} more documents")
    else:
        print("   (No indexed documents found)")

    print("\n 🧩 FIRST 10 CHUNK IDs & METADATA:")
    if sample_points:
        for idx, pt in enumerate(sample_points, start=1):
            chunk_id = pt["chunk_id"]
            doc_name = pt["document_name"]
            section = pt["section_title"]
            pages = ", ".join(str(p) for p in pt["page_numbers"]) if pt["page_numbers"] else "1"
            print(f"   [{idx:2d}] Chunk ID: {chunk_id}")
            print(f"        Doc: {doc_name} | Page(s): {pages} | Section: {section}")
    else:
        print("   (No vector points found)")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    col_name = sys.argv[1] if len(sys.argv) > 1 else settings.QDRANT_COLLECTION_NAME
    debug_qdrant_storage(col_name)
