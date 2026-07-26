"""
db/checkins.py
--------------
All database operations for the checkins table.
One checkin record per client per day.
"""

from db.client import supabase
from typing import Optional
from datetime import date


def get_today(client_id: str) -> Optional[dict]:
    """Get today's checkin record for a client. Returns None if not yet created."""
    today = date.today().isoformat()
    res = (
        supabase.table("checkins")
        .select("*")
        .eq("client_id", client_id)
        .eq("checkin_date", today)
        .execute()
    )
    data = res.data or []
    return data[0] if data else None


def sent_today(client_id: str) -> bool:
    """Returns True if the daily check-in message was already sent today."""
    return get_today(client_id) is not None


def create_today(client_id: str) -> dict:
    """
    Create a blank checkin record for today.
    Called right after the bot sends the daily check-in message.
    Status starts as 'no_response' until client replies.
    """
    today = date.today().isoformat()
    res = supabase.table("checkins").insert({
        "client_id": client_id,
        "checkin_date": today,
        "adherence_status": "no_response",
    }).execute()
    return res.data[0]


def update_today(
    client_id: str,
    client_message: Optional[str] = None,
    ai_reply: Optional[str] = None,
    adherence_status: Optional[str] = None,
    energy_level: Optional[int] = None,
    caretaker_note: Optional[str] = None,
) -> dict:
    """
    Update today's checkin record with AI classification results.
    Called after AI processes the client's reply.
    """
    today = date.today().isoformat()
    data = {}
    if client_message is not None:
        data["client_message"] = client_message
    if ai_reply is not None:
        data["ai_reply"] = ai_reply
    if adherence_status is not None:
        data["adherence_status"] = adherence_status
    if energy_level is not None:
        data["energy_level"] = energy_level
    if caretaker_note is not None:
        data["caretaker_note"] = caretaker_note

    res = (
        supabase.table("checkins")
        .update(data)
        .eq("client_id", client_id)
        .eq("checkin_date", today)
        .execute()
    )
    return res.data[0] if res.data else {}


def override_status(
    client_id: str,
    status: str,
    nutritionist_id: str,
    checkin_date: Optional[str] = None,
) -> dict:
    """
    Nutritionist manually overrides the AI's adherence classification.
    Called from the web app when doctor clicks On Track / Partial / Off Track.
    """
    from datetime import datetime, timezone
    target_date = checkin_date or date.today().isoformat()
    res = (
        supabase.table("checkins")
        .update({
            "override_status": status,
            "override_by": nutritionist_id,
            "override_at": datetime.now(timezone.utc).isoformat(),
        })
        .eq("client_id", client_id)
        .eq("checkin_date", target_date)
        .execute()
    )
    return res.data[0] if res.data else {}


def get_recent(client_id: str, limit: int = 7) -> list:
    """Get the last N checkin records for a client. Used for progress display."""
    res = (
        supabase.table("checkins")
        .select("*")
        .eq("client_id", client_id)
        .order("checkin_date", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


def get_active_status(checkin: dict) -> str:
    """
    Returns the effective adherence status.
    If nutritionist has overridden, use that. Otherwise use AI's classification.
    """
    return checkin.get("override_status") or checkin.get("adherence_status") or "no_response"


def get_weekly_stats(client_id: str) -> dict:
    """
    Computes summary stats for the last 7 days.
    Returns: { on_track: N, partial: N, off_track: N, no_response: N, consistency_pct: float }
    """
    records = get_recent(client_id, limit=7)
    counts = {"on_track": 0, "partial": 0, "off_track": 0, "no_response": 0}
    for r in records:
        status = get_active_status(r)
        if status in counts:
            counts[status] += 1

    total = len(records)
    responded = counts["on_track"] + counts["partial"] + counts["off_track"]
    consistency_pct = round((responded / total * 100) if total > 0 else 0, 1)

    return {**counts, "consistency_pct": consistency_pct, "total_days": total}
