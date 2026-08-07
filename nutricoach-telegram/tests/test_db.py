"""
tests/test_db.py
----------------
Tests for database operations.
These tests require a valid .env with Supabase credentials.
"""

import os
import pytest

# Skip all tests if no Supabase credentials
pytestmark = pytest.mark.skipif(
    not os.getenv("SUPABASE_URL"),
    reason="No Supabase credentials in .env"
)


def test_supabase_client_creation():
    """Check that Supabase client can be created."""
    from db.client import supabase
    assert supabase is not None


def test_nutritionists_table_accessible():
    """Check that nutritionists table is accessible."""
    from db.client import supabase
    res = supabase.table("nutritionists").select("id").limit(1).execute()
    assert hasattr(res, "data")


def test_clients_table_accessible():
    """Check that clients table is accessible."""
    from db.client import supabase
    res = supabase.table("clients").select("id").limit(1).execute()
    assert hasattr(res, "data")


def test_messages_table_accessible():
    """Check that messages table is accessible."""
    from db.client import supabase
    res = supabase.table("messages").select("id").limit(1).execute()
    assert hasattr(res, "data")
