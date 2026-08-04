import shutil
from typing import Annotated, List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_team
from app.config import settings
from app.database.models import TeamModel
from app.database.sqlite import get_db
from app.schemas.document import DocumentMetadataResponse, DocumentUploadResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("", response_model=List[DocumentMetadataResponse])
async def list_documents(
    current_team: Annotated[TeamModel, Depends(get_current_team)],
    db: Annotated[Session, Depends(get_db)]
) -> List[DocumentMetadataResponse]:
    """Lists metadata for all documents uploaded by the authenticated Team."""
    return DocumentService.list_team_documents(db, current_team.id)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: Annotated[UploadFile, File(...)],
    current_team: Annotated[TeamModel, Depends(get_current_team)],
    db: Annotated[Session, Depends(get_db)]
) -> DocumentUploadResponse:
    """Uploads document file and stores its metadata (without AI processing)."""
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    destination_path = settings.UPLOAD_DIR / f"{current_team.id}_{file.filename}"

    with destination_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = destination_path.stat().st_size
    doc_record = DocumentService.save_document_metadata(
        db=db,
        team_id=current_team.id,
        filename=file.filename,
        file_path=str(destination_path),
        file_size=file_size,
        content_type=file.content_type or "application/octet-stream"
    )

    return DocumentUploadResponse(
        message="Document uploaded successfully",
        document=doc_record
    )


@router.get("/{doc_id}", response_model=DocumentMetadataResponse)
async def get_document_metadata(
    doc_id: int,
    current_team: Annotated[TeamModel, Depends(get_current_team)],
    db: Annotated[Session, Depends(get_db)]
) -> DocumentMetadataResponse:
    """Retrieves document metadata by ID for the authenticated Team."""
    doc = DocumentService.get_document_by_id(db, doc_id, current_team.id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied"
        )
    return doc
