from typing import List, Optional
from sqlalchemy.orm import Session

from app.database.models import DocumentModel
from app.utils.logging import logger


class DocumentService:
    """Service handling document metadata and file storage operations."""

    @staticmethod
    def save_document_metadata(
        db: Session,
        team_id: int,
        filename: str,
        file_path: str,
        file_size: int,
        content_type: str
    ) -> DocumentModel:
        """Stores metadata for an uploaded document in the database.

        Args:
            db: Database session.
            team_id: Uploading team ID.
            filename: Original file name.
            file_path: Filesystem destination path.
            file_size: File size in bytes.
            content_type: File MIME type.

        Returns:
            DocumentModel: Persisted document record.
        """
        doc = DocumentModel(
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            content_type=content_type,
            team_id=team_id
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        logger.info(f"Saved document '{filename}' (ID: {doc.id}) for Team ID {team_id}.")
        return doc

    @staticmethod
    def get_document_by_id(db: Session, doc_id: int, team_id: int) -> Optional[DocumentModel]:
        """Retrieves a document metadata record owned by a team.

        Args:
            db: Database session.
            doc_id: Document ID.
            team_id: Team ID for owner verification.

        Returns:
            Optional[DocumentModel]: Document record or None.
        """
        return db.query(DocumentModel).filter(
            DocumentModel.id == doc_id,
            DocumentModel.team_id == team_id
        ).first()

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
