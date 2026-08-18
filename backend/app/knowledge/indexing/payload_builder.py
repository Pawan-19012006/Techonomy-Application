"""Payload Builder for constructing structured Qdrant payloads from KnowledgeChunk objects."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.knowledge.exceptions import PayloadBuilderError
from app.knowledge.models.embedding import Embedding
from app.knowledge.models.indexed_chunk import IndexedChunk
from app.knowledge.models.knowledge_chunk import KnowledgeChunk
from app.utils.logging import logger


class PayloadBuilder:
    """Serializes KnowledgeChunk and document metadata into standardized Qdrant payload dictionaries."""

    @classmethod
    def build_payload(
        cls,
        chunk: KnowledgeChunk,
        document_name: Optional[str] = None,
        version: str = "1.0",
    ) -> Dict[str, Any]:
        """Constructs a comprehensive Qdrant payload dictionary from a KnowledgeChunk object.

        Args:
            chunk (KnowledgeChunk): Target chunk.
            document_name (Optional[str]): Document filename or title.
            version (str): Payload schema version string (default '1.0').

        Returns:
            Dict[str, Any]: Serialized payload dictionary.

        Raises:
            PayloadBuilderError: If serialization fails.
        """
        try:
            page_start = min(chunk.page_numbers) if chunk.page_numbers else 1
            page_end = max(chunk.page_numbers) if chunk.page_numbers else 1

            doc_name = (
                document_name
                or chunk.metadata.get("filename")
                or chunk.metadata.get("document_name")
                or f"Document_{chunk.document_id[:8]}"
            )

            doc_type = (
                chunk.metadata.get("document_type")
                or ("instruction" if "instruction" in doc_name.lower() or "guide" in doc_name.lower() else "company")
            )
            visibility = "user_visible" if doc_type == "company" else "internal"
            source_type = "official_company_document" if doc_type == "company" else "analytical_instruction"

            payload = {
                "document_id": chunk.document_id,
                "document_name": doc_name,
                "document_type": doc_type,
                "visibility": visibility,
                "source_type": source_type,
                "chunk_id": chunk.chunk_id,
                "page_start": page_start,
                "page_end": page_end,
                "page_numbers": chunk.page_numbers,
                "section_title": chunk.section_title,
                "section_type": chunk.section_type,
                "hierarchy_level": chunk.hierarchy_level,
                "reading_order": chunk.reading_order,
                "estimated_tokens": chunk.estimated_tokens,
                "character_count": chunk.char_count,
                "content": chunk.content,
                "metadata": {
                    **dict(chunk.metadata),
                    "document_type": doc_type,
                    "visibility": visibility,
                    "source_type": source_type,
                },
                "version": version,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            return payload

        except Exception as e:
            logger.error(f"Payload serialization failed for Chunk '{chunk.chunk_id}': {e}")
            raise PayloadBuilderError(f"Failed to build payload for chunk '{chunk.chunk_id}': {str(e)}") from e

    @classmethod
    def build_indexed_chunk(
        cls,
        chunk: KnowledgeChunk,
        embedding: Embedding,
        document_name: Optional[str] = None,
    ) -> IndexedChunk:
        """Combines a KnowledgeChunk, document_name, and Embedding into an IndexedChunk domain object.

        Args:
            chunk (KnowledgeChunk): KnowledgeChunk object.
            embedding (Embedding): Vector embedding object.
            document_name (Optional[str]): Document filename or title.

        Returns:
            IndexedChunk: Combined IndexedChunk object.
        """
        payload = cls.build_payload(chunk, document_name=document_name)
        return IndexedChunk(embedding=embedding, payload=payload)

    @classmethod
    def build_indexed_chunks(
        cls,
        chunks: List[KnowledgeChunk],
        embeddings: List[Embedding],
        document_name: Optional[str] = None,
    ) -> List[IndexedChunk]:
        """Builds IndexedChunk domain objects from paired chunk and embedding lists.

        Args:
            chunks (List[KnowledgeChunk]): List of KnowledgeChunk objects.
            embeddings (List[Embedding]): Paired list of Embedding objects.
            document_name (Optional[str]): Document filename or title.

        Returns:
            List[IndexedChunk]: List of IndexedChunk domain objects.
        """
        if len(chunks) != len(embeddings):
            raise PayloadBuilderError(
                f"Mismatch between chunks count ({len(chunks)}) and embeddings count ({len(embeddings)})"
            )

        indexed_chunks: List[IndexedChunk] = []
        for chk, emb in zip(chunks, embeddings):
            indexed_chunks.append(cls.build_indexed_chunk(chk, emb, document_name=document_name))

        return indexed_chunks
