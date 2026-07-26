"""
api/routes/queries.py
---------------------
Pending query endpoints:
GET  /queries               — Get all pending queries for this nutritionist
POST /queries/:id/resolve   — Mark query resolved + optionally send reply
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from api.middleware import get_current_user
from db.client import supabase

router = APIRouter()


# ── Request models ───────────────────────────────────────────────────────────

class ResolveQuery(BaseModel):
    doctor_reply: Optional[str] = None


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("")
def get_pending_queries(user: dict = Depends(get_current_user)):
    """Get all pending queries for this nutritionist."""
    res = (
        supabase.table("pending_queries")
        .select("*, clients(full_name, program_type)")
        .eq("nutritionist_id", user["id"])
        .eq("status", "pending")
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


@router.get("/all")
def get_all_queries(user: dict = Depends(get_current_user)):
    """Get all queries (pending + resolved) for this nutritionist."""
    res = (
        supabase.table("pending_queries")
        .select("*, clients(full_name, program_type)")
        .eq("nutritionist_id", user["id"])
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


@router.post("/{query_id}/resolve")
def resolve_query(
    query_id: str,
    req: ResolveQuery,
    user: dict = Depends(get_current_user),
):
    """Mark a query as resolved. Optionally include a reply."""
    from datetime import datetime, timezone

    # Verify the query belongs to this nutritionist
    existing = (
        supabase.table("pending_queries")
        .select("*")
        .eq("id", query_id)
        .eq("nutritionist_id", user["id"])
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Query not found")

    query = existing.data[0]

    if query["status"] != "pending":
        raise HTTPException(status_code=400, detail="Query already resolved")

    # Get client info for Telegram group
    client_res = (
        supabase.table("clients")
        .select("telegram_group_id, full_name")
        .eq("id", query["client_id"])
        .execute()
    )
    client_info = client_res.data[0] if client_res.data else {}
    group_id = client_info.get("telegram_group_id")
    client_name = client_info.get("full_name", "Client")

    # Update query
    update_data = {
        "status": "resolved",
        "resolved_at": datetime.now(timezone.utc).isoformat(),
    }
    if req.doctor_reply:
        update_data["doctor_reply"] = req.doctor_reply

    supabase.table("pending_queries").update(update_data).eq("id", query_id).execute()

    # If doctor provided a reply, save to messages and notify the Telegram group
    if req.doctor_reply:
        # Save to messages table
        supabase.table("messages").insert({
            "client_id": query["client_id"],
            "sender_role": "nutritionist",
            "sender_name": user.get("full_name", "Doctor"),
            "content": req.doctor_reply,
        }).execute()

        # Send notification to Telegram group
        if group_id:
            try:
                import os
                import requests
                bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
                if bot_token:
                    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    payload = {
                        "chat_id": group_id,
                        "text": f"Doctor's reply to your question:\n\n{req.doctor_reply}",
                    }
                    resp = requests.post(url, json=payload, timeout=10)
                    if resp.ok:
                        print(f"[REPLY] Doctor replied to {client_name} in group {group_id}")
                    else:
                        print(f"[REPLY] Telegram API error: {resp.text}")
            except Exception as e:
                print(f"Failed to notify Telegram group: {e}")

    return {"message": "Query resolved"}
