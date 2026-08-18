"""Comprehensive unit tests for the Event Knowledge-Base Reset Workflow (scripts/reset_event.py).

Uses mocks for Qdrant client, CollectionManager, and IngestionPipeline to prevent network calls
or mutation of production Qdrant collections during test execution.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from app.knowledge.models.index_result import IndexResult
from scripts.reset_event import discover_pdfs, main, reset_and_index_event


@pytest.fixture
def temp_docs_dir(tmp_path):
    """Creates a temporary documents directory with mock PDF files."""
    docs_dir = tmp_path / "documents"
    docs_dir.mkdir()
    pdf1 = docs_dir / "company_handbook.pdf"
    pdf2 = docs_dir / "event_rules.pdf"
    pdf3 = docs_dir / "technical_manual.pdf"
    pdf1.write_bytes(b"%PDF-1.4 Mock PDF 1 Content")
    pdf2.write_bytes(b"%PDF-1.4 Mock PDF 2 Content")
    pdf3.write_bytes(b"%PDF-1.4 Mock PDF 3 Content")
    return docs_dir


def test_discover_pdfs_returns_sorted_pdf_paths(temp_docs_dir):
    """1. Test PDF discovery automatically finds and sorts all *.pdf files."""
    pdfs = discover_pdfs(temp_docs_dir)
    assert len(pdfs) == 3
    assert [p.name for p in pdfs] == [
        "company_handbook.pdf",
        "event_rules.pdf",
        "technical_manual.pdf",
    ]


def test_no_pdfs_aborts_safely(tmp_path):
    """2. Test empty PDF directory aborts safely without deleting collection."""
    empty_dir = tmp_path / "empty_docs"
    empty_dir.mkdir()

    with patch("scripts.reset_event.QdrantClientWrapper") as mock_qdrant:
        success = reset_and_index_event(documents_dir=empty_dir, auto_confirm=True)
        assert success is False
        mock_qdrant.assert_not_called()


def test_user_answers_no_aborts_reset(temp_docs_dir):
    """3. Test user answering 'N' aborts without modifying Qdrant."""
    with patch("builtins.input", return_value="n"), \
         patch("scripts.reset_event.QdrantClientWrapper") as mock_qdrant:
        success = reset_and_index_event(documents_dir=temp_docs_dir, auto_confirm=False)
        assert success is False
        mock_qdrant.assert_not_called()


def test_user_answers_yes_triggers_reset(temp_docs_dir):
    """4. Test user answering 'Y' proceeds with collection recreation and ingestion."""
    mock_wrapper = MagicMock()
    mock_wrapper.collection_info.return_value = {"status": "green", "points_count": 127}
    mock_wrapper.count_vectors.return_value = 127
    mock_wrapper.get_indexed_documents.return_value = [
        "company_handbook.pdf",
        "event_rules.pdf",
        "technical_manual.pdf",
    ]

    mock_collection_mgr = MagicMock()
    mock_collection_mgr.ensure_collection.return_value = True

    mock_pipeline = MagicMock()
    mock_pipeline.process_pdf_to_index.return_value = IndexResult(
        documents_indexed=1,
        chunks_indexed=5,
        vectors_uploaded=5,
        collection_name="company_knowledge",
        embedding_dimension=384,
        processing_time=0.1,
    )

    with patch("builtins.input", return_value="y"), \
         patch("scripts.reset_event.QdrantClientWrapper", return_value=mock_wrapper), \
         patch("scripts.reset_event.CollectionManager", return_value=mock_collection_mgr), \
         patch("scripts.reset_event.EmbeddingGenerator") as mock_embedder_cls, \
         patch("scripts.reset_event.IngestionPipeline", return_value=mock_pipeline):

        mock_embedder_cls.return_value.get_dimension.return_value = 384
        success = reset_and_index_event(documents_dir=temp_docs_dir, auto_confirm=False)

        assert success is True
        mock_collection_mgr.ensure_collection.assert_called_once_with(
            embedding_dimension=384,
            recreate=True,
        )
        assert mock_pipeline.process_pdf_to_index.call_count == 3


def test_all_discovered_pdfs_passed_to_pipeline(temp_docs_dir):
    """5. Test every discovered PDF is processed through IngestionPipeline."""
    mock_wrapper = MagicMock()
    mock_wrapper.collection_info.return_value = {"status": "green", "points_count": 50}
    mock_wrapper.count_vectors.return_value = 50
    mock_wrapper.get_indexed_documents.return_value = [
        "company_handbook.pdf",
        "event_rules.pdf",
        "technical_manual.pdf",
    ]

    mock_collection_mgr = MagicMock()
    mock_pipeline = MagicMock()
    mock_pipeline.process_pdf_to_index.return_value = IndexResult(
        documents_indexed=1,
        chunks_indexed=2,
        vectors_uploaded=2,
        collection_name="company_knowledge",
        embedding_dimension=384,
        processing_time=0.05,
    )

    with patch("scripts.reset_event.QdrantClientWrapper", return_value=mock_wrapper), \
         patch("scripts.reset_event.CollectionManager", return_value=mock_collection_mgr), \
         patch("scripts.reset_event.EmbeddingGenerator") as mock_embedder_cls, \
         patch("scripts.reset_event.IngestionPipeline", return_value=mock_pipeline):

        mock_embedder_cls.return_value.get_dimension.return_value = 384
        success = reset_and_index_event(documents_dir=temp_docs_dir, auto_confirm=True)

        assert success is True
        called_files = [call.kwargs["file_path"].name for call in mock_pipeline.process_pdf_to_index.call_args_list]
        assert called_files == ["company_handbook.pdf", "event_rules.pdf", "technical_manual.pdf"]


def test_failed_pdf_produces_non_zero_failure(temp_docs_dir):
    """6. Test single PDF failure causes reset script to return False (exit code 1)."""
    mock_wrapper = MagicMock()
    mock_collection_mgr = MagicMock()
    mock_pipeline = MagicMock()
    mock_pipeline.process_pdf_to_index.side_effect = RuntimeError("PDF page extraction error")

    with patch("scripts.reset_event.QdrantClientWrapper", return_value=mock_wrapper), \
         patch("scripts.reset_event.CollectionManager", return_value=mock_collection_mgr), \
         patch("scripts.reset_event.EmbeddingGenerator") as mock_embedder_cls, \
         patch("scripts.reset_event.IngestionPipeline", return_value=mock_pipeline):

        mock_embedder_cls.return_value.get_dimension.return_value = 384
        success = reset_and_index_event(documents_dir=temp_docs_dir, auto_confirm=True)

        assert success is False


def test_verification_detects_missing_or_unexpected_documents(temp_docs_dir):
    """7. Test post-ingestion verification fails if document list does not match PDFs."""
    mock_wrapper = MagicMock()
    mock_wrapper.collection_info.return_value = {"status": "green", "points_count": 50}
    mock_wrapper.count_vectors.return_value = 50
    # Missing technical_manual.pdf
    mock_wrapper.get_indexed_documents.return_value = ["company_handbook.pdf", "event_rules.pdf"]

    mock_collection_mgr = MagicMock()
    mock_pipeline = MagicMock()
    mock_pipeline.process_pdf_to_index.return_value = IndexResult(
        documents_indexed=1,
        chunks_indexed=2,
        vectors_uploaded=2,
        collection_name="company_knowledge",
        embedding_dimension=384,
        processing_time=0.05,
    )

    with patch("scripts.reset_event.QdrantClientWrapper", return_value=mock_wrapper), \
         patch("scripts.reset_event.CollectionManager", return_value=mock_collection_mgr), \
         patch("scripts.reset_event.EmbeddingGenerator") as mock_embedder_cls, \
         patch("scripts.reset_event.IngestionPipeline", return_value=mock_pipeline):

        mock_embedder_cls.return_value.get_dimension.return_value = 384
        success = reset_and_index_event(documents_dir=temp_docs_dir, auto_confirm=True)

        assert success is False


def test_script_import_has_no_side_effects():
    """8. Test importing reset_event module does not touch Qdrant or delete collections."""
    with patch("scripts.reset_event.QdrantClientWrapper") as mock_qdrant:
        import scripts.reset_event  # noqa: F401
        mock_qdrant.assert_not_called()


def test_repeated_execution_recreates_collection_each_time(temp_docs_dir):
    """9. Test repeated script execution recreates collection each time (non-additive)."""
    mock_wrapper = MagicMock()
    mock_wrapper.collection_info.return_value = {"status": "green", "points_count": 10}
    mock_wrapper.count_vectors.return_value = 10
    mock_wrapper.get_indexed_documents.return_value = [
        "company_handbook.pdf",
        "event_rules.pdf",
        "technical_manual.pdf",
    ]

    mock_collection_mgr = MagicMock()
    mock_pipeline = MagicMock()

    with patch("scripts.reset_event.QdrantClientWrapper", return_value=mock_wrapper), \
         patch("scripts.reset_event.CollectionManager", return_value=mock_collection_mgr), \
         patch("scripts.reset_event.EmbeddingGenerator") as mock_embedder_cls, \
         patch("scripts.reset_event.IngestionPipeline", return_value=mock_pipeline):

        mock_embedder_cls.return_value.get_dimension.return_value = 384

        # Run 1
        reset_and_index_event(documents_dir=temp_docs_dir, auto_confirm=True)
        # Run 2
        reset_and_index_event(documents_dir=temp_docs_dir, auto_confirm=True)

        # Verify ensure_collection(recreate=True) was called twice
        assert mock_collection_mgr.ensure_collection.call_count == 2
        for call in mock_collection_mgr.ensure_collection.call_args_list:
            assert call.kwargs["recreate"] is True


def test_main_cli_exit_code():
    """10. Test main() CLI wrapper exits with code 1 on failure."""
    with patch("scripts.reset_event.reset_and_index_event", return_value=False), \
         pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
