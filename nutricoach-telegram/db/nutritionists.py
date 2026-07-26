"""
db/nutritionists.py
-------------------
All database operations for the nutritionists table.
"""

from db.client import supabase
from typing import Optional


def get_by_id(nutritionist_id: str) -> Optional[dict]:
    """Fetch a nutritionist by their UUID."""
    res = supabase.table("nutritionists").select("*").eq("id", nutritionist_id).execute()
    data = res.data or []
    return data[0] if data else None


def get_by_email(email: str) -> Optional[dict]:
    """Fetch a nutritionist by email address. Used for login."""
    res = supabase.table("nutritionists").select("*").eq("email", email).execute()
    data = res.data or []
    return data[0] if data else None


def get_by_telegram_id(telegram_user_id: int) -> Optional[dict]:
    """Fetch a nutritionist by their Telegram account ID."""
    res = (
        supabase.table("nutritionists")
        .select("*")
        .eq("telegram_user_id", telegram_user_id)
        .execute()
    )
    data = res.data or []
    return data[0] if data else None


def get_all(status: Optional[str] = None) -> list:
    """
    Fetch all nutritionists. Optionally filter by status.
    status can be: 'pending', 'active', 'paused', 'expired'
    """
    query = supabase.table("nutritionists").select("*")
    if status:
        query = query.eq("status", status)
    res = query.order("created_at", desc=True).execute()
    return res.data or []


def create(data: dict) -> dict:
    """
    Create a new nutritionist account.
    data should include: full_name, clinic_name, email, password (hashed)
    Status defaults to 'pending' (must be approved by admin).
    """
    res = supabase.table("nutritionists").insert(data).execute()
    return res.data[0]


def update(nutritionist_id: str, data: dict) -> dict:
    """Update any fields of a nutritionist record."""
    res = (
        supabase.table("nutritionists")
        .update(data)
        .eq("id", nutritionist_id)
        .execute()
    )
    return res.data[0]


def approve(nutritionist_id: str, admin_id: str) -> dict:
    """
    Admin approves a pending nutritionist.
    Sets status to 'active' and records who approved and when.
    """
    from datetime import datetime, timezone
    return update(nutritionist_id, {
        "status": "active",
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "approved_by": admin_id,
    })


def pause(nutritionist_id: str) -> dict:
    """Pause a nutritionist — bot stops for all their clients."""
    return update(nutritionist_id, {"status": "paused"})


def reactivate(nutritionist_id: str) -> dict:
    """Reactivate a paused nutritionist."""
    return update(nutritionist_id, {"status": "active"})


def set_telegram_id(nutritionist_id: str, telegram_user_id: int) -> dict:
    """Link a nutritionist's web account to their Telegram account."""
    return update(nutritionist_id, {"telegram_user_id": telegram_user_id})


def is_active(nutritionist_id: str) -> bool:
    """Quick check — is this nutritionist allowed to operate?"""
    nut = get_by_id(nutritionist_id)
    return nut is not None and nut.get("status") == "active"
