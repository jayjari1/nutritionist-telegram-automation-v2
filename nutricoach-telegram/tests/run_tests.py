"""
tests/run_tests.py
------------------
Simple test runner for NutriCoach.
Run with: python -m tests.run_tests
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import setup_logging, get_logger

setup_logging()
logger = get_logger("tests")

import unittest

# Discover and load tests
loader = unittest.TestLoader()
suite = loader.discover(os.path.dirname(__file__), pattern="test_*.py")

# Run tests
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

# Exit with appropriate code
sys.exit(0 if result.wasSuccessful() else 1)
