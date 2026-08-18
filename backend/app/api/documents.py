"""API router for discovering, querying, and serving official company competition documents."""

import os
from pathlib import Path
from typing import List, Set
from urllib.parse import unquote
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
import fitz  # PyMuPDF for reliable PDF page count extraction

from app.config import settings
from app.schemas.document import DocumentResponse
from app.utils.logging import logger

router = APIRouter(prefix="/documents", tags=["Documents"])


def get_company_documents_directories() -> List[Path]:
    """Returns list of authorized directories containing official COMPANY competition documents."""
    dirs = [
        settings.BASE_DIR / "data" / "documents" / "company",
        settings.BASE_DIR / "app" / "documents" / "company",
    ]
    valid_dirs = []
    for d in dirs:
        if d.exists() and d.is_dir():
            valid_dirs.append(d)

    if not valid_dirs:
        # Fallback to creating data/documents/company
        fallback = settings.BASE_DIR / "data" / "documents" / "company"
        fallback.mkdir(parents=True, exist_ok=True)
        valid_dirs.append(fallback)
    return valid_dirs


def get_instruction_filenames() -> Set[str]:
    """Returns set of internal instruction filenames to prohibit public access."""
    instruction_dir = settings.BASE_DIR / "data" / "documents" / "instructions"
    names = set()
    if instruction_dir.exists() and instruction_dir.is_dir():
        for p in instruction_dir.glob("*"):
            if p.is_file():
                names.add(p.name.lower())
    return names


def find_document_file(document_id: str) -> Path:
    """Safely resolves document_id to a verified company PDF file path.

    Strict Security Enforcement:
    1. Prevents path traversal attempts (HTTP 400).
    2. Prohibits access to internal instruction documents (HTTP 403).
    3. Restricts resolution strictly to authorized COMPANY document directories.
    """
    if not document_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document identifier.",
        )

    # Decode URL-encoded filename (e.g. 6%20-%20revised.pdf -> 6 - revised.pdf)
    decoded_name = unquote(document_id).strip()
    clean_name = os.path.basename(decoded_name).strip()

    # Path traversal check
    if not clean_name or ".." in decoded_name or "/" in decoded_name or "\\" in decoded_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document identifier or path traversal attempt.",
        )

    # Instruction document check
    lower_name = clean_name.lower()
    instruction_names = get_instruction_filenames()
    if lower_name in instruction_names or "instruction" in lower_name or "blueprint" in lower_name:
        logger.warning(f"[SECURITY BLOCKED] Unauthorized attempt to access internal instruction document: '{clean_name}'")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Internal instruction documents are restricted.",
        )

    # Resolve against authorized company document directories ONLY
    for doc_dir in get_company_documents_directories():
        candidate = (doc_dir / clean_name).resolve()
        try:
            doc_dir_resolved = doc_dir.resolve()
            if candidate.is_relative_to(doc_dir_resolved) and candidate.exists() and candidate.is_file():
                return candidate
        except Exception:
            continue

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Company document '{clean_name}' not found.",
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


@router.get("", response_model=List[DocumentResponse], summary="List Official Company Event Documents")
async def list_documents() -> List[DocumentResponse]:
    """Discovers and returns metadata for official COMPANY competition documents ONLY."""
    documents: List[DocumentResponse] = []
    seen_filenames: Set[str] = set()
    instruction_names = get_instruction_filenames()

    for doc_dir in get_company_documents_directories():
        for file_path in doc_dir.glob("*"):
            if file_path.is_file() and not file_path.name.startswith("."):
                fname_lower = file_path.name.lower()
                # Security filter: Never expose instruction files or hidden files
                if fname_lower in seen_filenames or fname_lower in instruction_names or "instruction" in fname_lower:
                    continue
                seen_filenames.add(fname_lower)

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


@router.get("/{document_id}", response_model=DocumentResponse, summary="Get Company Document Metadata")
async def get_document_metadata(document_id: str) -> DocumentResponse:
    """Retrieves metadata for a specific official company document."""
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


@router.get("/{document_id}/file", summary="Serve Official Company Document File")
async def serve_document_file(document_id: str):
    """Safely streams raw company PDF document file for in-app PDF viewer."""
    file_path = find_document_file(document_id)
    media_type = "application/pdf" if file_path.suffix.lower() == ".pdf" else "application/octet-stream"
    headers = {
        "Content-Disposition": f'inline; filename="{file_path.name}"',
        "Access-Control-Expose-Headers": "Content-Disposition, Content-Length, Content-Type, Accept-Ranges",
        "Accept-Ranges": "bytes",
    }
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type=media_type,
        headers=headers,
    )
