import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.knowledge.indexing.collection_manager import CollectionManager


def inspect():
    print("=" * 80)
    print("STEP 2: QDRANT COLLECTIONS INSPECTION")
    print("=" * 80)

    # 1. Company Collection
    company_cm = CollectionManager(collection_name=settings.QDRANT_COMPANY_COLLECTION_NAME)
    client = company_cm.client_wrapper.connect()
    comp_info = company_cm.get_info()
    comp_count = comp_info.get("points_count", 0) if isinstance(comp_info, dict) else 0

    print(f"\n📁 COMPANY COLLECTION: '{settings.QDRANT_COMPANY_COLLECTION_NAME}'")
    print(f"   - Total Points (Vectors): {comp_count}")

    if comp_count > 0:
        points, _ = client.scroll(collection_name=settings.QDRANT_COMPANY_COLLECTION_NAME, limit=30)
        docs = set()
        for p in points:
            dname = p.payload.get("document_name") or p.payload.get("filename")
            if dname:
                docs.add(dname)

        print(f"   - Unique Documents ({len(docs)}): {sorted(list(docs))}")
        print("   - Sample Point Metadata:")
        if points:
            sample_pl = points[0].payload
            print(f"       doc_name: {sample_pl.get('document_name')}")
            print(f"       doc_type: {sample_pl.get('document_type')}")
            print(f"       visibility: {sample_pl.get('visibility')}")
            print(f"       source_type: {sample_pl.get('source_type')}")
            print(f"       pages: {sample_pl.get('page_numbers')}")
            print(f"       snippet: {sample_pl.get('content', '')[:100]}...")
    else:
        print("   ⚠️ WARNING: COMPANY COLLECTION IS COMPLETELY EMPTY (0 POINTS)!")

    # 2. Instruction Collection
    inst_cm = CollectionManager(collection_name=settings.QDRANT_INSTRUCTION_COLLECTION_NAME)
    inst_info = inst_cm.get_info()
    inst_count = inst_info.get("points_count", 0) if isinstance(inst_info, dict) else 0

    print(f"\n📁 INSTRUCTION COLLECTION: '{settings.QDRANT_INSTRUCTION_COLLECTION_NAME}'")
    print(f"   - Total Points (Vectors): {inst_count}")

    if inst_count > 0:
        points, _ = client.scroll(collection_name=settings.QDRANT_INSTRUCTION_COLLECTION_NAME, limit=30)
        docs = set()
        for p in points:
            dname = p.payload.get("document_name") or p.payload.get("filename")
            if dname:
                docs.add(dname)

        print(f"   - Unique Documents ({len(docs)}): {sorted(list(docs))}")
        print("   - Sample Point Metadata:")
        if points:
            sample_pl = points[0].payload
            print(f"       doc_name: {sample_pl.get('document_name')}")
            print(f"       doc_type: {sample_pl.get('document_type')}")
            print(f"       visibility: {sample_pl.get('visibility')}")
            print(f"       source_type: {sample_pl.get('source_type')}")
            print(f"       pages: {sample_pl.get('page_numbers')}")
            print(f"       snippet: {sample_pl.get('content', '')[:100]}...")
    else:
        print("   ⚠️ WARNING: INSTRUCTION COLLECTION IS COMPLETELY EMPTY (0 POINTS)!")

    print("=" * 80)


if __name__ == "__main__":
    inspect()
