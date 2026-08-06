"""Embedding domain model representing a vector embedding for a chunk."""

from typing import List
from pydantic import BaseModel, Field


class Embedding(BaseModel):
    """Represents a vector embedding generated for a document chunk.

    Attributes:
        chunk_id (str): UUID reference to parent KnowledgeChunk.
        vector (List[float]): Dense float vector values.
        dimension (int): Vector dimensionality (e.g. 384).
        normalized (bool): Indicates if vector is normalized to unit length.
    """

    chunk_id: str = Field(..., description="Parent chunk UUID reference")
    vector: List[float] = Field(..., description="Dense float vector representation")
    dimension: int = Field(..., description="Dimensionality length of vector")
    normalized: bool = Field(default=False, description="Flag indicating if vector is L2 normalized")
