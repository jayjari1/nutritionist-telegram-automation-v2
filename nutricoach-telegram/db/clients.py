"""
db/clients.py
-------------
All database operations for the clients table.
"""

from db.client import supabase
from typing import Optional
from datetime import date, time, timedelta
from logger import get_logger

logger = get_logger("db.clients")


def get_by_id(client_id: str) -> Optional[dict]:
    """Fetch a client by UUID."""
    res = supabase.table("clients").select("*").eq("id", client_id).execute()
    data = res.data or []
    return data[0] if data else None


def get_by_telegram_user_id(telegram_user_id: int) -> Optional[dict]:
    """Fetch a client by their Telegram account ID."""
    res = (
        supabase.table("clients")
        .select("*")
        .eq("telegram_user_id", telegram_user_id)
        .execute()
    )
    data = res.data or []
    return data[0] if data else None


def get_by_group_id(group_id: int) -> Optional[dict]:
    """Fetch a client by their Telegram group chat ID."""
    logger.debug(f"get_by_group_id({group_id}) - querying Supabase...")
    res = (
        supabase.table("clients")
        .select("*")
        .eq("telegram_group_id", group_id)
        .execute()
    )
    data = res.data or []
    logger.debug(f"get_by_group_id result: {len(data)} rows")
    return data[0] if data else None


def get_all_for_nutritionist(nutritionist_id: str, status: Optional[str] = None) -> list:
    """
    Get all clients belonging to a nutritionist.
    Optionally filter by status: 'active', 'paused', 'expired', 'completed'
    """
    query = (
        supabase.table("clients")
        .select("*")
        .eq("nutritionist_id", nutritionist_id)
    )
    if status:
        query = query.eq("status", status)
    res = query.order("created_at", desc=True).execute()
    return res.data or []


def get_due_for_checkin(current_time_str: str) -> list:
    """
    Returns all active clients whose check-in time matches current_time_str (HH:MM format).
    Used by the scheduler every minute.
    """
    res = (
        supabase.table("clients")
        .select("*")
        .eq("status", "active")
        .eq("checkin_time", current_time_str + ":00")  # DB stores as HH:MM:SS
        .execute()
    )
    return res.data or []


def create(data: dict) -> dict:
    """
    Add a new client.
    Required fields: nutritionist_id, full_name, telegram_phone, program_type,
                     program_duration, program_start, checkin_time, diet_chart
    Auto-computes: program_end = program_start + program_duration days
    """
    # Compute end date
    if "program_start" in data and "program_duration" in data:
        start = date.fromisoformat(data["program_start"])
        data["program_end"] = (start + timedelta(days=data["program_duration"])).isoformat()

    res = supabase.table("clients").insert(data).execute()
    return res.data[0]


def update(client_id: str, data: dict) -> dict:
    """Update any fields of a client record."""
    res = supabase.table("clients").update(data).eq("id", client_id).execute()
    return res.data[0]


def set_telegram_ids(client_id: str, telegram_user_id: int, group_id: int) -> dict:
    """Called after client joins the Telegram group — store their IDs."""
    return update(client_id, {
        "telegram_user_id": telegram_user_id,
        "telegram_group_id": group_id,
    })


def set_group_id(client_id: str, group_id: int) -> dict:
    """Store the Telegram group ID after the group is created."""
    return update(client_id, {"telegram_group_id": group_id})


def set_status(client_id: str, status: str) -> dict:
    """
    Update a client's plan status.
    status: 'active', 'paused', 'expired', 'completed'
    """
    return update(client_id, {"status": status})


def get_expiring_soon(days_threshold: int = 7) -> list:
    """
    Returns all active clients whose program ends within `days_threshold` days.
    Used by the scheduler to send expiry warnings.
    """
    from datetime import datetime, timezone
    today = date.today()
    threshold_date = (today + timedelta(days=days_threshold)).isoformat()

    res = (
        supabase.table("clients")
        .select("*, nutritionists(full_name, telegram_user_id)")
        .eq("status", "active")
        .lte("program_end", threshold_date)
        .gte("program_end", today.isoformat())
        .execute()
    )
    return res.data or []


def days_remaining(client: dict) -> int:
    """Helper: how many days left in this client's program."""
    if not client.get("program_end"):
        return 0
    end = date.fromisoformat(client["program_end"])
    delta = (end - date.today()).days
    return max(0, delta)
