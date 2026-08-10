"""Automated Pytest unit test suite for Knowledge Engine Phase 4 (Knowledge Indexing Engine)."""

from pathlib import Path
import pytest
from app.config import settings
from app.knowledge.indexing.collection_manager import CollectionManager
from app.knowledge.indexing.embedder import EmbeddingGenerator
from app.knowledge.indexing.embedding_batcher import EmbeddingBatcher
from app.knowledge.indexing.embedding_normalizer import EmbeddingNormalizer
from app.knowledge.indexing.index_manager import IndexManager
from app.knowledge.indexing.payload_builder import PayloadBuilder
from app.knowledge.indexing.qdrant_client import QdrantClientWrapper
from app.knowledge.ingestion.ingest import IngestionPipeline, index_pdf
from app.knowledge.models.embedding import Embedding
from app.knowledge.models.index_result import IndexResult
from app.knowledge.models.indexed_chunk import IndexedChunk
from app.knowledge.models.knowledge_chunk import KnowledgeChunk
from scripts.test_structure import generate_structured_sample_pdf


@pytest.fixture
def sample_chunk() -> KnowledgeChunk:
    """Fixture returning a sample KnowledgeChunk."""
    return KnowledgeChunk(
        document_id="doc-test-100",
        page_numbers=[1, 2],
        section_title="Executive Summary",
        section_type="heading",
        hierarchy_level=1,
        reading_order=0,
        content="Techonomy Enterprise Knowledge Intelligence Platform test content.",
        estimated_tokens=15,
        metadata={"filename": "test_doc.pdf", "page_numbers": [1, 2]},
    )


def test_phase4_models(sample_chunk: KnowledgeChunk):
    """Tests Embedding, IndexedChunk, and IndexResult model instantiations."""
    emb = Embedding(
        chunk_id=sample_chunk.chunk_id,
        vector=[0.1, 0.2, 0.3],
        dimension=3,
        normalized=True,
    )
    assert emb.chunk_id == sample_chunk.chunk_id
    assert emb.dimension == 3
    assert emb.normalized is True

    payload = PayloadBuilder.build_payload(sample_chunk, document_name="test_doc.pdf")
    ichk = IndexedChunk(embedding=emb, payload=payload)
    assert ichk.payload["document_id"] == "doc-test-100"
    assert ichk.payload["document_name"] == "test_doc.pdf"

    res = IndexResult(
        documents_indexed=1,
        chunks_indexed=1,
        vectors_uploaded=1,
        collection_name="company_knowledge",
        embedding_dimension=384,
        processing_time=0.5,
    )
    assert res.documents_indexed == 1
    assert res.vectors_uploaded == 1


def test_embedding_batcher(sample_chunk: KnowledgeChunk):
    """Tests EmbeddingBatcher chunk grouping."""
    chunks = [sample_chunk] * 70
    batches = EmbeddingBatcher.create_batches(chunks, batch_size=32)

    assert len(batches) == 3
    assert len(batches[0]) == 32
    assert len(batches[1]) == 32
    assert len(batches[2]) == 6


def test_embedding_generator_and_normalizer(sample_chunk: KnowledgeChunk):
    """Tests local EmbeddingGenerator and EmbeddingNormalizer L2 unit normalization."""
    embedder = EmbeddingGenerator(model_name=settings.EMBEDDING_MODEL_NAME)
    dim = embedder.get_dimension()
    assert dim == 384

    raw_embeddings = embedder.generate_embeddings([sample_chunk])
    assert len(raw_embeddings) == 1
    assert raw_embeddings[0].dimension == 384
    assert raw_embeddings[0].normalized is False

    normalized_embeddings = EmbeddingNormalizer.normalize(raw_embeddings)
    assert len(normalized_embeddings) == 1
    assert normalized_embeddings[0].normalized is True

    # Verify L2 norm length is approximately 1.0
    vec = normalized_embeddings[0].vector
    norm_val = sum(x * x for x in vec) ** 0.5
    assert pytest.approx(norm_val, abs=1e-3) == 1.0


def test_qdrant_client_and_collection_manager(sample_chunk: KnowledgeChunk):
    """Tests QdrantClientWrapper, CollectionManager, and point upsert."""
    client_wrapper = QdrantClientWrapper()
    assert client_wrapper.health_check() is True

    coll_mgr = CollectionManager(
        client_wrapper=client_wrapper,
        collection_name="test_collection",
        distance_metric="Cosine",
    )
    coll_mgr.ensure_collection(embedding_dimension=384, recreate=True)

    emb = Embedding(
        chunk_id=sample_chunk.chunk_id,
        vector=[0.05] * 384,
        dimension=384,
        normalized=True,
    )
    indexed_chunk = PayloadBuilder.build_indexed_chunk(
        chunk=sample_chunk,
        embedding=emb,
        document_name="test_doc.pdf",
    )

    uploaded = client_wrapper.upsert_chunks(
        collection_name="test_collection",
        indexed_chunks=[indexed_chunk],
    )
    assert uploaded == 1

    info = client_wrapper.collection_info("test_collection")
    assert str(info.get("status")).lower() in ("green", "yellow", "ok")


def test_full_phase4_indexing_pipeline(tmp_path: Path):
    """Tests full end-to-end index_pdf pipeline."""
    pdf_file = tmp_path / "test_indexing_sample.pdf"
    generate_structured_sample_pdf(pdf_file)

    res = index_pdf(
        pdf_file,
        max_tokens=512,
        recreate_collection=True,
        collection_name="pytest_unit_test_collection",
    )

    assert isinstance(res, IndexResult)
    assert res.documents_indexed == 1
    assert res.chunks_indexed > 0
    assert res.vectors_uploaded == res.chunks_indexed
    assert res.embedding_dimension == 384
    assert res.processing_time > 0.0
