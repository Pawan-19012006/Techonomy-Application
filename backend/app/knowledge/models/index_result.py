"""IndexResult domain model summarizing indexing operation outcome."""

from pydantic import BaseModel, Field


class IndexResult(BaseModel):
    """Summarizes quantitative and operational metrics of an indexing operation.

    Attributes:
        documents_indexed (int): Number of distinct documents processed and indexed.
        chunks_indexed (int): Number of KnowledgeChunk objects indexed.
        vectors_uploaded (int): Total count of vector embeddings uploaded to Qdrant.
        collection_name (str): Target Qdrant collection name.
        embedding_dimension (int): Vector dimensionality (e.g. 384).
        processing_time (float): Elapsed time for full indexing pipeline execution (seconds).
    """

    documents_indexed: int = Field(default=0, description="Number of documents indexed")
    chunks_indexed: int = Field(default=0, description="Number of chunks indexed")
    vectors_uploaded: int = Field(default=0, description="Total vectors uploaded to Qdrant")
    collection_name: str = Field(..., description="Target Qdrant collection name")
    embedding_dimension: int = Field(..., description="Vector dimensionality")
    processing_time: float = Field(default=0.0, description="Processing execution time in seconds")
