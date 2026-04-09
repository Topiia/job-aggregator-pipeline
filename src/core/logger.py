"""
Structured logging for the Job Aggregator system.

Provides a pre-configured logger with:
  - Console handler (INFO level, colorized)
  - Rotating file handler (DEBUG level, plain text)

Usage:
    from src.core.logger import get_logger

    logger = get_logger(__name__)
    logger.info("Scraping started")
    logger.error("HTTP 429 from %s", url)
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from src.core.config import config


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_MAX_LOG_BYTES = 5 * 1024 * 1024  # 5 MB per log file
_BACKUP_COUNT = 3                  # keep 3 rotated copies

# ANSI color codes for console output
_COLORS = {
    "DEBUG":    "\033[90m",    # grey
    "INFO":     "\033[36m",    # cyan
    "WARNING":  "\033[33m",    # yellow
    "ERROR":    "\033[31m",    # red
    "CRITICAL": "\033[1;31m",  # bold red
}
_RESET = "\033[0m"


# ---------------------------------------------------------------------------
# Colorized console formatter
# ---------------------------------------------------------------------------

class _ColorFormatter(logging.Formatter):
    """Formatter that injects ANSI color codes based on log level."""

    def __init__(self) -> None:
        super().__init__(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)

    def format(self, record: logging.LogRecord) -> str:
        color = _COLORS.get(record.levelname, "")
        formatted = super().format(record)
        if color:
            return f"{color}{formatted}{_RESET}"
        return formatted


# ---------------------------------------------------------------------------
# Plain file formatter
# ---------------------------------------------------------------------------

class _PlainFormatter(logging.Formatter):
    """Standard formatter without color codes for log files."""

    def __init__(self) -> None:
        super().__init__(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)


# ---------------------------------------------------------------------------
# Logger setup — runs once on first import
# ---------------------------------------------------------------------------

_initialized = False


def _initialize_root_logger() -> None:
    """
    Configure the root logger with console and file handlers.

    Called once automatically. Subsequent calls are no-ops.
    """
    global _initialized
    if _initialized:
        return
    _initialized = True

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove any existing handlers to avoid duplicates on reimport
    root_logger.handlers.clear()

    # ── Console handler ──────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(_ColorFormatter())
    root_logger.addHandler(console_handler)

    # ── File handler ─────────────────────────────────────────────────
    log_dir = os.path.dirname(config.LOG_PATH)
    os.makedirs(log_dir, exist_ok=True)

    file_handler = RotatingFileHandler(
        filename=config.LOG_PATH,
        maxBytes=_MAX_LOG_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(_PlainFormatter())
    root_logger.addHandler(file_handler)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger with console and file handlers attached.

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A configured ``logging.Logger`` instance.
    """
    _initialize_root_logger()
    return logging.getLogger(name)
