"""ChunkStatistics domain model representing quantitative chunk metrics."""

from pydantic import BaseModel, Field


class ChunkStatistics(BaseModel):
    """Calculated quantitative statistics for generated KnowledgeChunk objects.

    Attributes:
        total_chunks (int): Total count of valid generated chunks.
        average_chunk_size (float): Average character count per chunk.
        largest_chunk (int): Maximum character count among chunks.
        smallest_chunk (int): Minimum character count among chunks.
        average_tokens (float): Average estimated token count per chunk.
        total_tokens (int): Aggregate estimated token count across all chunks.
    """

    total_chunks: int = Field(default=0, description="Total count of valid generated chunks")
    average_chunk_size: float = Field(default=0.0, description="Average character count per chunk")
    largest_chunk: int = Field(default=0, description="Maximum character length among chunks")
    smallest_chunk: int = Field(default=0, description="Minimum character length among chunks")
    average_tokens: float = Field(default=0.0, description="Average estimated token count per chunk")
    total_tokens: int = Field(default=0, description="Aggregate estimated token count across all chunks")
