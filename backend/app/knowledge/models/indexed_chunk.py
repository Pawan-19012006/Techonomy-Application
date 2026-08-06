"""IndexedChunk domain model combining vector embedding and Qdrant payload."""

from typing import Any, Dict
from pydantic import BaseModel, Field

from app.knowledge.models.embedding import Embedding


class IndexedChunk(BaseModel):
    """Represents a fully prepared chunk ready for vector database indexing.

    Attributes:
        embedding (Embedding): Vector embedding domain object.
        payload (Dict[str, Any]): Comprehensive metadata payload for Qdrant storage.
    """

    embedding: Embedding = Field(..., description="Vector embedding object")
    payload: Dict[str, Any] = Field(..., description="Qdrant metadata payload dictionary")
