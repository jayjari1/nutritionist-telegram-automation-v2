"""
api/routes/messages.py
----------------------
Message history endpoints:
GET  /clients/:id/messages  — Get all messages for a client
"""

from fastapi import APIRouter, Depends, HTTPException

from api.middleware import get_current_user
from db.client import supabase

router = APIRouter()


def _verify_client_ownership(client_id: str, nutritionist_id: str) -> bool:
    """Check if this client belongs to this nutritionist."""
    res = (
        supabase.table("clients")
        .select("id")
        .eq("id", client_id)
        .eq("nutritionist_id", nutritionist_id)
        .execute()
    )
    return bool(res.data)


@router.get("/{client_id}/messages")
def get_client_messages(
    client_id: str,
    user: dict = Depends(get_current_user),
):
    """Get all messages for a client (chronological order)."""
    if not _verify_client_ownership(client_id, user["id"]):
        raise HTTPException(status_code=404, detail="Client not found")

    res = (
        supabase.table("messages")
        .select("*")
        .eq("client_id", client_id)
        .order("sent_at", desc=False)
        .execute()
    )
    return res.data or []
