"""Pydantic schemas for Document API endpoints."""

from typing import Optional
from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    """Schema representing an official event document."""

    id: str = Field(..., description="Document identifier (filename)")
    filename: str = Field(..., description="Document filename")
    file_type: str = Field(default="PDF", description="File format type (PDF, Text, etc.)")
    size_bytes: int = Field(default=0, description="File size in bytes")
    pages: int = Field(default=1, description="Total page count of document")
    status: str = Field(default="Available", description="Availability status (Available, Indexed)")
