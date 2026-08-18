"""API router for discovering, querying, and serving official event competition documents."""

import os
from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
import fitz  # PyMuPDF for reliable PDF page count extraction

from app.config import settings
from app.schemas.document import DocumentResponse
from app.utils.logging import logger

router = APIRouter(prefix="/documents", tags=["Documents"])


def get_documents_directories() -> List[Path]:
    """Returns list of valid directories containing official event documents."""
    dirs = [
        settings.BASE_DIR / "app" / "documents",
        settings.BASE_DIR / "data" / "documents",
    ]
    valid_dirs = []
    for d in dirs:
        if d.exists() and d.is_dir():
            valid_dirs.append(d)
    if not valid_dirs:
        # Fallback to creating data/documents
        fallback = settings.BASE_DIR / "data" / "documents"
        fallback.mkdir(parents=True, exist_ok=True)
        valid_dirs.append(fallback)
    return valid_dirs


def find_document_file(document_id: str) -> Path:
    """Safely resolves document_id to a verified file path within authorized document directories.

    Prevents directory traversal attacks by validating strict containment.
    """
    clean_name = os.path.basename(document_id).strip()
    if not clean_name or ".." in clean_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document identifier.",
        )

    for doc_dir in get_documents_directories():
        candidate = (doc_dir / clean_name).resolve()
        try:
            doc_dir_resolved = doc_dir.resolve()
            if candidate.is_relative_to(doc_dir_resolved) and candidate.exists() and candidate.is_file():
                return candidate
        except Exception:
            continue

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Document '{clean_name}' not found.",
    )


def extract_pdf_pages(file_path: Path) -> int:
    """Extracts page count from PDF using PyMuPDF."""
    if file_path.suffix.lower() != ".pdf":
        return 1
    try:
        doc = fitz.open(file_path)
        page_count = len(doc)
        doc.close()
        return max(1, page_count)
    except Exception as e:
        logger.warning(f"Could not read PDF page count for {file_path.name}: {e}")
        return 1


@router.get("", response_model=List[DocumentResponse], summary="List Official Event Documents")
async def list_documents() -> List[DocumentResponse]:
    """Discovers and returns metadata for all official competition documents in authorized storage directories."""
    documents: List[DocumentResponse] = []
    seen_filenames = set()

    for doc_dir in get_documents_directories():
        for file_path in doc_dir.glob("*"):
            if file_path.is_file() and not file_path.name.startswith("."):
                if file_path.name in seen_filenames:
                    continue
                seen_filenames.add(file_path.name)

                pages = extract_pdf_pages(file_path)
                file_type = file_path.suffix.lstrip(".").upper() or "PDF"
                size_bytes = file_path.stat().st_size

                documents.append(
                    DocumentResponse(
                        id=file_path.name,
                        filename=file_path.name,
                        file_type=file_type,
                        size_bytes=size_bytes,
                        pages=pages,
                        status="Available",
                    )
                )

    return sorted(documents, key=lambda d: d.filename.lower())


@router.get("/{document_id}", response_model=DocumentResponse, summary="Get Document Metadata")
async def get_document_metadata(document_id: str) -> DocumentResponse:
    """Retrieves metadata for a specific official document."""
    file_path = find_document_file(document_id)
    pages = extract_pdf_pages(file_path)
    file_type = file_path.suffix.lstrip(".").upper() or "PDF"
    size_bytes = file_path.stat().st_size

    return DocumentResponse(
        id=file_path.name,
        filename=file_path.name,
        file_type=file_type,
        size_bytes=size_bytes,
        pages=pages,
        status="Available",
    )


@router.get("/{document_id}/file", summary="Serve Official Document File")
async def serve_document_file(document_id: str):
    """Safely streams raw PDF document file for in-app PDF viewer."""
    file_path = find_document_file(document_id)
    media_type = "application/pdf" if file_path.suffix.lower() == ".pdf" else "application/octet-stream"
    headers = {
        "Content-Disposition": f'inline; filename="{file_path.name}"',
        "Access-Control-Expose-Headers": "Content-Disposition, Content-Length, Content-Type",
    }
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type=media_type,
        headers=headers,
    )
