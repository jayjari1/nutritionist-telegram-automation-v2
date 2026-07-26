"""
api/routes/checkins.py
----------------------
Check-in endpoints:
GET  /clients/:id/checkins       — Get all checkins for a client
GET  /clients/:id/checkins/today — Get today's checkin
PATCH /clients/:id/checkins/today — Override today's adherence status
"""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from api.middleware import get_current_user
from db.client import supabase

router = APIRouter()


# ── Request models ───────────────────────────────────────────────────────────

class OverrideCheckin(BaseModel):
    adherence_status: str  # 'on_track', 'partial', 'off_track', 'no_response'


# ── Helpers ──────────────────────────────────────────────────────────────────

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


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/{client_id}/checkins")
def get_checkins(client_id: str, user: dict = Depends(get_current_user)):
    """Get all check-in records for a client (most recent first)."""
    if not _verify_client_ownership(client_id, user["id"]):
        raise HTTPException(status_code=404, detail="Client not found")

    res = (
        supabase.table("checkins")
        .select("*")
        .eq("client_id", client_id)
        .order("checkin_date", desc=True)
        .execute()
    )
    return res.data or []


@router.get("/{client_id}/checkins/today")
def get_today_checkin(client_id: str, user: dict = Depends(get_current_user)):
    """Get today's check-in record."""
    if not _verify_client_ownership(client_id, user["id"]):
        raise HTTPException(status_code=404, detail="Client not found")

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


@router.patch("/{client_id}/checkins/today")
def override_today_checkin(
    client_id: str,
    req: OverrideCheckin,
    user: dict = Depends(get_current_user),
):
    """Override today's adherence status (nutritionist manual override)."""
    if not _verify_client_ownership(client_id, user["id"]):
        raise HTTPException(status_code=404, detail="Client not found")

    today = date.today().isoformat()

    # Check if today's checkin exists
    existing = (
        supabase.table("checkins")
        .select("id")
        .eq("client_id", client_id)
        .eq("checkin_date", today)
        .execute()
    )

    if not existing.data:
        raise HTTPException(status_code=404, detail="No checkin record for today")

    # Update with override
    from datetime import datetime, timezone
    supabase.table("checkins").update({
        "override_status": req.adherence_status,
        "override_by": user["id"],
        "override_at": datetime.now(timezone.utc).isoformat(),
    }).eq("client_id", client_id).eq("checkin_date", today).execute()

    return {"message": f"Adherence overridden to {req.adherence_status}"}
