"""
db/queries.py
-------------
All database operations for the pending_queries table.
A pending query is created when AI escalates a client message to the nutritionist.
"""

from db.client import supabase
from typing import Optional


def create(
    client_id: str,
    nutritionist_id: str,
    client_message: str,
    ai_assessment: str,
    ai_interim_reply: str,
) -> dict:
    """
    Create a new pending query (AI escalation).
    Called when AI decides it cannot handle a message and needs doctor review.
    """
    res = supabase.table("pending_queries").insert({
        "client_id": client_id,
        "nutritionist_id": nutritionist_id,
        "client_message": client_message,
        "ai_assessment": ai_assessment,
        "ai_interim_reply": ai_interim_reply,
        "status": "pending",
    }).execute()
    return res.data[0]


def get_pending_for_nutritionist(nutritionist_id: str) -> list:
    """
    Get all unresolved queries for a nutritionist.
    Used by web app Alerts screen and Doctor Bot.
    """
    res = (
        supabase.table("pending_queries")
        .select("*, clients(full_name, program_type)")
        .eq("nutritionist_id", nutritionist_id)
        .eq("status", "pending")
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


def get_pending_for_client(client_id: str) -> Optional[dict]:
    """
    Get the most recent unresolved query for a specific client.
    Used to check if there's an active escalation before showing chat banner.
    """
    res = (
        supabase.table("pending_queries")
        .select("*")
        .eq("client_id", client_id)
        .eq("status", "pending")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def resolve(query_id: str, doctor_reply: Optional[str] = None, resolved_by: str = "doctor") -> dict:
    """
    Mark a pending query as resolved.
    Called when nutritionist replies from web app or directly in Telegram group.
    resolved_by: 'doctor' or 'ai'
    """
    from datetime import datetime, timezone
    status = "resolved" if resolved_by == "doctor" else "ai_handled"
    data = {
        "status": status,
        "resolved_at": datetime.now(timezone.utc).isoformat(),
    }
    if doctor_reply:
        data["doctor_reply"] = doctor_reply

    res = (
        supabase.table("pending_queries")
        .update(data)
        .eq("id", query_id)
        .execute()
    )
    return res.data[0] if res.data else {}


def auto_resolve_on_doctor_message(client_id: str, doctor_reply: str) -> Optional[dict]:
    """
    When the nutritionist sends any message to a Telegram group,
    auto-resolve any open pending query for that client.
    Returns the resolved query dict, or None if nothing was resolved.
    """
    open_query = get_pending_for_client(client_id)
    if open_query:
        resolve(open_query["id"], doctor_reply=doctor_reply, resolved_by="doctor")
        return open_query
    return None
