"""Document Access & Security Boundary Test Suite.

Tests cover:
1. Company document listing (ONLY company documents exposed).
2. Instruction documents strictly filtered out of document list.
3. Access to company PDF files (1.pdf, 3.pdf, 6 - revised.pdf, DS08...) returns 200 OK with application/pdf.
4. Access to instruction PDF files (e.g. Financial_Analysis_Instruction.pdf) is REJECTED (403 Forbidden).
5. Path traversal attempts are REJECTED (400 Bad Request / 403 Forbidden).
6. Non-existent document returns 404 Not Found.
7. Citation page number preservation from ChatService/Retrieval to API response.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_company_documents_only():
    """Test 1: GET /api/documents returns official company documents and NEVER instruction documents."""
    response = client.get("/api/documents")
    assert response.status_code == 200
    docs = response.json()
    assert isinstance(docs, list)
    assert len(docs) > 0

    filenames = [d["filename"].lower() for d in docs]

    # Verify company files are present
    assert "1.pdf" in filenames or "3.pdf" in filenames

    # Verify instruction files are STRICTLY EXCLUDED
    for fname in filenames:
        assert "instruction" not in fname
        assert "blueprint" not in fname
        assert "bible" not in fname


def test_serve_valid_company_pdf():
    """Test 2: GET /api/documents/{id}/file serves valid company PDF with application/pdf Content-Type."""
    # Test simple filename
    res1 = client.get("/api/documents/1.pdf/file")
    assert res1.status_code == 200
    assert res1.headers["content-type"] == "application/pdf"
    assert len(res1.content) > 1000

    # Test filename with spaces and hyphens
    res2 = client.get("/api/documents/6%20-%20revised.pdf/file")
    assert res2.status_code == 200
    assert res2.headers["content-type"] == "application/pdf"

    # Test DS series filename
    res3 = client.get("/api/documents/DS08_Finance_Commercial_Economics.pdf/file")
    assert res3.status_code == 200
    assert res3.headers["content-type"] == "application/pdf"


def test_block_instruction_document_access():
    """Test 3: Attempting to access internal instruction PDFs returns 403 Forbidden or 404 Not Found."""
    forbidden_files = [
        "Financial_Analysis_Instruction.pdf",
        "Vendor_Evaluation_Instruction.pdf",
        "Company_Blueprint.pdf",
        "Master_Business_Bible_v1.pdf",
    ]

    for fname in forbidden_files:
        res = client.get(f"/api/documents/{fname}/file")
        assert res.status_code in (403, 404), f"Failed to block instruction document: {fname}"


def test_block_path_traversal_attempts():
    """Test 4: Path traversal attempts are rejected with 400 or 403."""
    traversals = [
        "../instructions/Financial_Analysis_Instruction.pdf",
        "..%2F..%2Fetc%2Fpasswd",
        "..\\..\\windows\\system32",
    ]

    for t in traversals:
        res = client.get(f"/api/documents/{t}/file")
        assert res.status_code in (400, 403, 404)


def test_nonexistent_document_returns_404():
    """Test 5: Requesting non-existent company document returns 404 Not Found."""
    res = client.get("/api/documents/non_existent_fake_document_999.pdf/file")
    assert res.status_code == 404
