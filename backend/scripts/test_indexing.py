"""Terminal Test Script for Phase 4 Knowledge Indexing Engine.

Pipeline Flow:
PDF -> Parser -> Cleaner -> Structure Analyzer -> Hierarchy Builder -> Metadata Builder -> Statistics Generator -> Semantic Chunker -> Chunk Optimizer -> Chunk Validator -> Embedding Generator -> Payload Builder -> Qdrant Index
"""

from pathlib import Path
import sys
import time

# Add project root directory to python path for standalone script execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.knowledge.indexing.collection_manager import CollectionManager
from app.knowledge.indexing.embedder import EmbeddingGenerator
from app.knowledge.indexing.embedding_batcher import EmbeddingBatcher
from app.knowledge.indexing.embedding_normalizer import EmbeddingNormalizer
from app.knowledge.indexing.payload_builder import PayloadBuilder
from app.knowledge.indexing.qdrant_client import QdrantClientWrapper
from app.knowledge.ingestion.ingest import IngestionPipeline
from scripts.test_structure import generate_structured_sample_pdf


def main():
    """Main CLI execution routine for Phase 4 Knowledge Indexing Engine testing."""
    print("\n" + "=" * 80)
    print(" 🚀 TECHONOMY KNOWLEDGE INDEXING ENGINE - PHASE 4 TEST")
    print("=" * 80 + "\n")

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
        pipeline = IngestionPipeline()

        # Step 1: Run Phase 1 + 2 + 3 (Ingestion, Structuring, Optimization)
        print("⚙️ Executing Ingestion, Structuring, & Optimization Pipeline (Phases 1-3)...")
        chunks, chunk_stats = pipeline.process_pdf_to_chunks(pdf_path, max_tokens=512)
        print(f"   ✓ Generated {len(chunks)} valid KnowledgeChunk objects.")

        # Step 2: Initialize Indexing Components
        print("\n⚙️ Initializing Local Embedding Generator & Vector Database...")
        embedder = EmbeddingGenerator(model_name=settings.EMBEDDING_MODEL_NAME)
        dimension = embedder.get_dimension()
        client_wrapper = QdrantClientWrapper()
        collection_mgr = CollectionManager(client_wrapper=client_wrapper)

        # Ensure collection exists
        collection_mgr.ensure_collection(embedding_dimension=dimension, recreate=True)

        # Step 3: Batching & Embedding Generation
        batches = EmbeddingBatcher.create_batches(chunks, batch_size=settings.EMBEDDING_BATCH_SIZE)
        
        t0 = time.time()
        raw_embeddings = embedder.generate_embeddings(chunks, batch_size=settings.EMBEDDING_BATCH_SIZE)
        embed_time = time.time() - t0
        avg_embed_time_per_chunk = round((embed_time / len(chunks)) * 1000, 2) if chunks else 0.0

        # Step 4: L2 Normalization
        normalized_embeddings = EmbeddingNormalizer.normalize(raw_embeddings)

        # Step 5: Payload Serialization
        indexed_chunks = PayloadBuilder.build_indexed_chunks(
            chunks=chunks,
            embeddings=normalized_embeddings,
            document_name=pdf_path.name,
        )

        # Step 6: Qdrant Vector Upsert
        uploaded_count = client_wrapper.upsert_chunks(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            indexed_chunks=indexed_chunks,
        )

        # Step 7: Collection Inspection & Verification
        info = client_wrapper.collection_info(settings.QDRANT_COLLECTION_NAME)

        # Print Output Summary
        print("\n" + "=" * 80)
        print(" 📊 KNOWLEDGE INDEXING ENGINE METRICS & SUMMARY")
        print("=" * 80)
        print(f" • Embedding Model Name:     {settings.EMBEDDING_MODEL_NAME}")
        print(f" • Embedding Dimension:      {dimension} dimensions")
        print(f" • Number of Chunks:         {len(chunks)} chunks")
        print(f" • Batch Count:              {len(batches)} batch(es) (size={settings.EMBEDDING_BATCH_SIZE})")
        print(f" • Total Embedding Time:     {embed_time:.3f} seconds")
        print(f" • Avg Embedding Time/Chunk: {avg_embed_time_per_chunk} ms/chunk")
        print(f" • Target Collection Name:   {settings.QDRANT_COLLECTION_NAME}")
        print(f" • Distance Metric:          {settings.QDRANT_DISTANCE_METRIC}")
        print(f" • Collection Status:        {info.get('status')}")
        print(f" • Vectors Uploaded:         {uploaded_count} vectors")
        print(f" • Total Collection Points:  {info.get('points_count')} points")
        print("-" * 80)

        # Print Sample Embedding Dimension & Vector Preview
        sample_vec = normalized_embeddings[0].vector if normalized_embeddings else []
        print("\n 📐 SAMPLE VECTOR EMBEDDING PREVIEW:")
        print(f"   • Vector Length:     {len(sample_vec)} floats")
        print(f"   • Is Normalized:     {normalized_embeddings[0].normalized}")
        print(f"   • First 5 Floats:    {sample_vec[:5]}")

        # Print Sample Payload
        sample_payload = indexed_chunks[0].payload if indexed_chunks else {}
        print("\n 📦 SAMPLE QDRANT PAYLOAD:")
        for k, v in sample_payload.items():
            if k == "content":
                preview_val = str(v).replace("\n", " ")[:90] + "..."
                print(f"   • {k:18s}: \"{preview_val}\"")
            else:
                print(f"   • {k:18s}: {v}")

        print("\n" + "=" * 80)
        print(" ✅ PHASE 4 KNOWLEDGE INDEXING PIPELINE TEST PASSED SUCCESSFULLY!")
        print("=" * 80 + "\n")

    except Exception as e:
        print("\n" + "=" * 80)
        print(f" ❌ PIPELINE TEST FAILED: {e}")
        print("=" * 80 + "\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
