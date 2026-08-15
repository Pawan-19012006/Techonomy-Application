"""Custom exceptions for the Techonomy Knowledge Engine."""


class KnowledgeEngineError(Exception):
    """Base exception for all Knowledge Engine operational errors."""
    pass


class PDFLoaderError(KnowledgeEngineError):
    """Raised when PDF loading or page text extraction fails."""
    pass


class DocumentParserError(KnowledgeEngineError):
    """Raised when document parsing or loader orchestration fails."""
    pass


class TextCleanerError(KnowledgeEngineError):
    """Raised when text cleaning or normalization fails."""
    pass


class StructureAnalyzerError(KnowledgeEngineError):
    """Raised when structural layout or element analysis fails."""
    pass


class HierarchyBuilderError(KnowledgeEngineError):
    """Raised when document hierarchy tree assembly fails."""
    pass


class MetadataBuilderError(KnowledgeEngineError):
    """Raised when metadata enrichment fails."""
    pass


class StatisticsGeneratorError(KnowledgeEngineError):
    """Raised when document statistics calculation fails."""
    pass


class SemanticChunkerError(KnowledgeEngineError):
    """Raised when semantic chunking fails."""
    pass


class ChunkOptimizerError(KnowledgeEngineError):
    """Raised when chunk optimization (merging/splitting) fails."""
    pass


class ChunkValidatorError(KnowledgeEngineError):
    """Raised when chunk validation encounters critical failures."""
    pass


class TokenEstimatorError(KnowledgeEngineError):
    """Raised when token estimation fails."""
    pass


class EmbeddingGeneratorError(KnowledgeEngineError):
    """Raised when local vector embedding generation fails."""
    pass


class EmbeddingBatcherError(KnowledgeEngineError):
    """Raised when chunk batch grouping fails."""
    pass


class EmbeddingNormalizerError(KnowledgeEngineError):
    """Raised when L2 vector normalization fails."""
    pass


class PayloadBuilderError(KnowledgeEngineError):
    """Raised when Qdrant payload serialization fails."""
    pass


class QdrantClientWrapperError(KnowledgeEngineError):
    """Raised when low-level Qdrant client operational calls fail."""
    pass


class CollectionManagerError(KnowledgeEngineError):
    """Raised when Qdrant collection creation, inspection, or verification fails."""
    pass


class IndexManagerError(KnowledgeEngineError):
    """Raised when full indexing pipeline orchestration fails."""
    pass


class QueryProcessorError(KnowledgeEngineError):
    """Raised when user query validation or normalization fails."""
    pass


class QueryEmbedderError(KnowledgeEngineError):
    """Raised when query vector embedding fails."""
    pass


class VectorSearchError(KnowledgeEngineError):
    """Raised when Qdrant vector similarity search fails."""
    pass


class SearchFilterError(KnowledgeEngineError):
    """Raised when metadata search filter construction fails."""
    pass


class RerankerError(KnowledgeEngineError):
    """Raised when search result reranking fails."""
    pass


class ContextBuilderError(KnowledgeEngineError):
    """Raised when context text assembly or citation generation fails."""
    pass


class RetrievalPipelineError(KnowledgeEngineError):
    """Raised when full retrieval pipeline orchestration fails."""
    pass


class PromptBuilderError(KnowledgeEngineError):
    """Raised when prompt construction or template formatting fails."""
    pass


class LLMServiceError(KnowledgeEngineError):
    """Base exception for all LLM generation operational failures."""
    pass


class OpenRouterAPIError(LLMServiceError):
    """Raised when OpenRouter API encounters HTTP, authentication, or payload errors."""
    pass


class LLMTimeoutError(LLMServiceError):
    """Raised when OpenRouter API call times out after configured threshold."""
    pass


class LLMQuotaExhaustedError(LLMServiceError):
    """Raised when all LLM capacity pools (Gemini primary and Nemotron fallback) are exhausted or unavailable."""
    pass


class ChatServiceError(KnowledgeEngineError):
    """Raised when ChatService orchestration fails."""
    pass

