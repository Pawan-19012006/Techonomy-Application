"""Search Filters module constructing Qdrant payload filters."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from qdrant_client.http import models as rest_models

from app.knowledge.exceptions import SearchFilterError
from app.utils.logging import logger


class SearchFilters(BaseModel):
    """Encapsulates document, section, page, and similarity filter parameters for vector search.

    Attributes:
        document_id (Optional[Union[str, List[str]]]): Filter by document UUID(s).
        page_numbers (Optional[Union[int, List[int]]]): Filter by page number(s).
        section_type (Optional[Union[str, List[str]]]): Filter by section type(s) (heading, paragraph, table, list).
        minimum_similarity (Optional[float]): Minimum similarity threshold filter.
        extra_metadata (Optional[Dict[str, Any]]): Arbitrary key-value metadata filter pairs for future expansion.
    """

    document_id: Optional[Union[str, List[str]]] = Field(default=None, description="Document ID or list of IDs")
    page_numbers: Optional[Union[int, List[int]]] = Field(default=None, description="Page number or list of page numbers")
    section_type: Optional[Union[str, List[str]]] = Field(default=None, description="Section type or list of section types")
    minimum_similarity: Optional[float] = Field(default=None, description="Minimum similarity threshold")
    extra_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Extra metadata key-value filters")

    def to_qdrant_filter(self) -> Optional[rest_models.Filter]:
        """Converts filter criteria into a native Qdrant rest_models.Filter object.

        Returns:
            Optional[rest_models.Filter]: Qdrant Filter object, or None if no filters applied.

        Raises:
            SearchFilterError: If filter construction fails.
        """
        must_conditions: List[rest_models.Condition] = []

        try:
            # Filter by document_id
            if self.document_id is not None:
                if isinstance(self.document_id, list):
                    must_conditions.append(
                        rest_models.FieldCondition(
                            key="document_id",
                            match=rest_models.MatchAny(any=self.document_id),
                        )
                    )
                else:
                    must_conditions.append(
                        rest_models.FieldCondition(
                            key="document_id",
                            match=rest_models.MatchValue(value=self.document_id),
                        )
                    )

            # Filter by page_numbers
            if self.page_numbers is not None:
                if isinstance(self.page_numbers, list):
                    must_conditions.append(
                        rest_models.FieldCondition(
                            key="page_numbers",
                            match=rest_models.MatchAny(any=self.page_numbers),
                        )
                    )
                else:
                    must_conditions.append(
                        rest_models.FieldCondition(
                            key="page_numbers",
                            match=rest_models.MatchValue(value=self.page_numbers),
                        )
                    )

            # Filter by section_type
            if self.section_type is not None:
                if isinstance(self.section_type, list):
                    must_conditions.append(
                        rest_models.FieldCondition(
                            key="section_type",
                            match=rest_models.MatchAny(any=self.section_type),
                        )
                    )
                else:
                    must_conditions.append(
                        rest_models.FieldCondition(
                            key="section_type",
                            match=rest_models.MatchValue(value=self.section_type),
                        )
                    )

            # Extra key-value metadata filters
            if self.extra_metadata:
                for k, v in self.extra_metadata.items():
                    if isinstance(v, list):
                        must_conditions.append(
                            rest_models.FieldCondition(
                                key=f"metadata.{k}",
                                match=rest_models.MatchAny(any=v),
                            )
                        )
                    else:
                        must_conditions.append(
                            rest_models.FieldCondition(
                                key=f"metadata.{k}",
                                match=rest_models.MatchValue(value=v),
                            )
                        )

            if not must_conditions:
                return None

            qdrant_filter = rest_models.Filter(must=must_conditions)
            logger.debug(f"Constructed Qdrant Filter with {len(must_conditions)} conditions.")
            return qdrant_filter

        except Exception as e:
            logger.error(f"Failed to build Qdrant search filter: {e}")
            raise SearchFilterError(f"Error constructing Qdrant search filter: {str(e)}") from e
