import logging
import sys
from pathlib import Path
from typing import Optional

from app.config import settings


def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """Configures and returns a structured logger.

    Supports both console logging and file logging under the logs directory.

    Args:
        name: Optional module name for the logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger_name = name or settings.PROJECT_NAME
    logger = logging.getLogger(logger_name)

    # Avoid duplicate handlers if already configured
    if logger.hasHandlers():
        return logger

    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Formatter configuration
    log_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    # File Handler
    try:
        settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(settings.LOG_DIR / "app.log", encoding="utf-8")
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
    except Exception as e:
        console_handler.setLevel(logging.WARNING)
        logger.warning(f"Could not initialize file logger at {settings.LOG_DIR}: {e}")

    return logger


logger: logging.Logger = setup_logger("Techonomy")
