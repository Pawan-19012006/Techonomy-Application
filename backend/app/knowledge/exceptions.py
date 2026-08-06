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
