"""
Structured logging for Insurance Policy Analyzer.

Provides consistent logging with request context and proper levels.
"""

import logging
import sys
from pathlib import Path
from typing import Any

# Default log format
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Package logger name
LOGGER_NAME = "bimabuddy"


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__). Defaults to package name.

    Returns:
        Configured Logger instance.
    """
    logger_name = f"{LOGGER_NAME}.{name}" if name else LOGGER_NAME
    logger = logging.getLogger(logger_name)

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        logger.addHandler(handler)
        logger.propagate = False

    return logger


def log_request(logger: logging.Logger, endpoint: str, extra: dict[str, Any] | None = None) -> None:
    """Log incoming API request."""
    logger.info("Request received", extra={"endpoint": endpoint, **(extra or {})})


def log_response(logger: logging.Logger, endpoint: str, status: int, duration_ms: float) -> None:
    """Log API response."""
    level = logging.WARNING if status >= 400 else logging.INFO
    logger.log(level, f"Response sent: {status}", extra={"endpoint": endpoint, "duration_ms": duration_ms})


def log_error(logger: logging.Logger, message: str, exc: Exception | None = None) -> None:
    """Log error with optional exception."""
    if exc:
        logger.exception("%s: %s", message, exc)
    else:
        logger.error(message)
