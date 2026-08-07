"""
tests/test_config.py
--------------------
Tests for configuration and environment variables.
"""

import os
import pytest


def test_env_file_exists():
    """Check that .env file exists."""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    assert os.path.exists(env_path), ".env file not found"


def test_config_imports():
    """Check that config module can be imported."""
    from config import TELEGRAM_BOT_TOKEN, SUPABASE_URL, GEMINI_API_KEY
    # Just check they exist (may be empty in test env)
    assert isinstance(TELEGRAM_BOT_TOKEN, str)
    assert isinstance(SUPABASE_URL, str)
    assert isinstance(GEMINI_API_KEY, str)


def test_logger_imports():
    """Check that logger module can be imported."""
    from logger import setup_logging, get_logger
    logger = get_logger("test")
    assert logger is not None
