"""RetrievalResult domain model summarizing the complete retrieval operation."""

from typing import List
from pydantic import BaseModel, Field

from app.knowledge.models.context_package import ContextPackage
from app.knowledge.models.processed_query import ProcessedQuery
from app.knowledge.models.search_result import SearchResult


class RetrievalResult(BaseModel):
    """Summarizes end-to-end execution metrics and objects from the Knowledge Retrieval Engine.

    Attributes:
        processed_query (ProcessedQuery): Cleaned and validated user query object.
        embedding_dimension (int): Vector dimension length (e.g. 384).
        top_k_searched (int): Number of initial top-k vector search results requested.
        top_n_reranked (int): Number of top-n reranked results selected.
        raw_search_results (List[SearchResult]): List of initial vector search matches.
        reranked_results (List[SearchResult]): List of reranked SearchResult matches.
        context_package (ContextPackage): Final synthesized ContextPackage object.
        processing_time (float): Total retrieval pipeline execution duration in seconds.
    """

    processed_query: ProcessedQuery = Field(..., description="Processed query object")
    embedding_dimension: int = Field(..., description="Vector embedding dimension")
    top_k_searched: int = Field(..., description="Top K vector search matches requested")
    top_n_reranked: int = Field(..., description="Top N reranked matches selected")
    raw_search_results: List[SearchResult] = Field(default_factory=list, description="Initial vector search results")
    reranked_results: List[SearchResult] = Field(default_factory=list, description="Reranked search results")
    context_package: ContextPackage = Field(..., description="Synthesized ContextPackage object")
    processing_time: float = Field(default=0.0, description="Elapsed execution time in seconds")
