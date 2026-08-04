import logging
from app.utils.logging import logger


class LoggingService:
    """Service wrapper for application logging operations."""

    @staticmethod
    def get_logger() -> logging.Logger:
        """Returns the central application logger instance."""
        return logger
