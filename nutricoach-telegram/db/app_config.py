"""
db/app_config.py
----------------
All database operations for the app_config table.
Stores all app configuration editable from admin UI.
"""

from db.client import supabase
from typing import Optional


def get_all() -> list:
    """Get all config entries."""
    res = supabase.table("app_config").select("*").order("category").execute()
    return res.data or []


def get_by_key(key: str) -> Optional[dict]:
    """Get a single config value by key."""
    res = supabase.table("app_config").select("*").eq("key", key).execute()
    data = res.data or []
    return data[0] if data else None


def get_value(key: str, default: str = "") -> str:
    """Get a config value as string. Returns default if not found."""
    entry = get_by_key(key)
    return entry["value"] if entry else default


def get_by_category(category: str) -> list:
    """Get all config entries for a category."""
    res = (
        supabase.table("app_config")
        .select("*")
        .eq("category", category)
        .order("key")
        .execute()
    )
    return res.data or []


def upsert(key: str, value: str, category: str = "general", description: str = "", is_secret: bool = False) -> dict:
    """Insert or update a config entry."""
    res = supabase.table("app_config").upsert({
        "key": key,
        "value": value,
        "category": category,
        "description": description,
        "is_secret": is_secret,
        "updated_at": "now()",
    }).execute()
    return res.data[0] if res.data else {}


def update_value(key: str, value: str) -> dict:
    """Update just the value of a config entry."""
    from datetime import datetime, timezone
    res = (
        supabase.table("app_config")
        .update({"value": value, "updated_at": datetime.now(timezone.utc).isoformat()})
        .eq("key", key)
        .execute()
    )
    return res.data[0] if res.data else {}


def delete_key(key: str) -> bool:
    """Delete a config entry."""
    supabase.table("app_config").delete().eq("key", key).execute()
    return True
