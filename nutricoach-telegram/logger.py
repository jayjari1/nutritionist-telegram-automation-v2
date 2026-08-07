"""
logger.py
---------
Centralized logging configuration.
Replaces all print() statements with proper logging.
Logs go to stdout (Railway captures these) with timestamps.
"""

import logging
import sys
from datetime import datetime


def setup_logging(level=logging.INFO):
    """
    Configure logging for the entire application.
    Call this once at startup.
    """
    # Create formatter with timestamp
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler that writes to stdout (Railway captures this)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    # Suppress noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    Usage: logger = get_logger("bot.command_handler")
    """
    return logging.getLogger(name)
