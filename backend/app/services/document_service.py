from pathlib import Path
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.models import DocumentModel
from app.utils.logging import logger


class DocumentService:
    """Service handling document metadata persistence and management."""

    @staticmethod
    def save_document_metadata(
        db: Session,
        team_id: int,
        filename: str,
        file_path: str,
        file_size: int,
        content_type: str,
        pages: int = 1,
        status: str = "ready"
    ) -> DocumentModel:
        """Stores metadata for an uploaded document in the database.

        Args:
            db: Database session.
            team_id: Uploading team ID.
            filename: Original file name.
            file_path: Filesystem destination path.
            file_size: File size in bytes.
            content_type: File MIME type.
            pages: Page count.
            status: Document processing status.

        Returns:
            DocumentModel: Persisted document record.
        """
        doc = DocumentModel(
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            content_type=content_type,
            pages=pages,
            status=status,
            team_id=team_id
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        logger.info(f"Saved document metadata '{filename}' (ID: {doc.id}) for Team ID {team_id}.")
        return doc

    @staticmethod
    def get_document_by_id(db: Session, doc_id: int, team_id: Optional[int] = None) -> Optional[DocumentModel]:
        """Retrieves a document record, optionally verifying owner team ID.

        Args:
            db: Database session.
            doc_id: Document ID.
            team_id: Optional Team ID for owner verification.

        Returns:
            Optional[DocumentModel]: Document record or None.
        """
        query = db.query(DocumentModel).filter(DocumentModel.id == doc_id)
        if team_id is not None:
            query = query.filter(DocumentModel.team_id == team_id)
        return query.first()

    @staticmethod
    def list_team_documents(db: Session, team_id: int) -> List[DocumentModel]:
        """Lists all document metadata uploaded by a team.

        Args:
            db: Database session.
            team_id: Team ID.

        Returns:
            List[DocumentModel]: List of document records.
        """
        return db.query(DocumentModel).filter(
            DocumentModel.team_id == team_id
        ).order_by(DocumentModel.uploaded_at.desc()).all()

    @staticmethod
    def list_all_documents(db: Session) -> List[DocumentModel]:
        """Lists all document metadata across all teams (Admin operation).

        Args:
            db: Database session.

        Returns:
            List[DocumentModel]: List of all document records.
        """
        return db.query(DocumentModel).order_by(DocumentModel.uploaded_at.desc()).all()

    @staticmethod
    def delete_document(db: Session, doc_id: int, team_id: int) -> bool:
        """Deletes a document metadata record and removes the file from disk if present.

        Args:
            db: Database session.
            doc_id: Target Document ID.
            team_id: Team ID owning the document.

        Returns:
            bool: True if deleted, False if not found or unauthorized.
        """
        doc = DocumentService.get_document_by_id(db, doc_id, team_id)
        if not doc:
            return False

        file_p = Path(doc.file_path)
        if file_p.exists():
            try:
                file_p.unlink()
            except Exception as e:
                logger.warning(f"Could not delete physical file at {doc.file_path}: {e}")

        db.delete(doc)
        db.commit()
        logger.info(f"Deleted document ID {doc_id} owned by Team ID {team_id}.")
        return True

    @staticmethod
    def count_team_documents(db: Session, team_id: int) -> int:
        """Counts total documents uploaded by a team.

        Args:
            db: Database session.
            team_id: Team ID.

        Returns:
            int: Document count.
        """
        return db.query(func.count(DocumentModel.id)).filter(DocumentModel.team_id == team_id).scalar() or 0
