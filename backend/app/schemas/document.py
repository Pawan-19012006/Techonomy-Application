from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DocumentMetadataResponse(BaseModel):
    """Schema for Document metadata response."""

    id: int
    filename: str
    file_path: str
    file_size: int
    content_type: str
    team_id: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentUploadResponse(BaseModel):
    """Response schema following document upload."""

    message: str
    document: DocumentMetadataResponse
