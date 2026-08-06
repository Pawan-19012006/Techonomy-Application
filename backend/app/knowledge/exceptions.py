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
