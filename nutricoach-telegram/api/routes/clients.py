"""
api/routes/clients.py
---------------------
Client management endpoints:
GET    /clients          — Get all clients for this nutritionist
GET    /clients/:id      — Get single client full profile
POST   /clients          — Add new client
PATCH  /clients/:id      — Update client info
DELETE /clients/:id      — Archive/deactivate client
"""

from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from api.middleware import get_current_user
from db.client import supabase

router = APIRouter()


# ── Request models ───────────────────────────────────────────────────────────

class ClientCreate(BaseModel):
    full_name: str
    telegram_phone: Optional[str] = None
    telegram_user_id: Optional[int] = None
    program_type: Optional[str] = "General Nutrition"
    program_duration: int = 30
    program_start: Optional[str] = None
    checkin_time: str = "19:00:00"
    diet_chart: Optional[str] = None
    caretaker_name: Optional[str] = None
    caretaker_telegram: Optional[int] = None


class ClientUpdate(BaseModel):
    full_name: Optional[str] = None
    telegram_phone: Optional[str] = None
    telegram_user_id: Optional[int] = None
    telegram_group_id: Optional[int] = None
    program_type: Optional[str] = None
    program_duration: Optional[int] = None
    program_start: Optional[str] = None
    checkin_time: Optional[str] = None
    diet_chart: Optional[str] = None
    caretaker_name: Optional[str] = None
    caretaker_telegram: Optional[int] = None
    status: Optional[str] = None


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("")
def get_clients(user: dict = Depends(get_current_user)):
    """Get all clients for this nutritionist."""
    res = (
        supabase.table("clients")
        .select("*")
        .eq("nutritionist_id", user["id"])
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


@router.get("/{client_id}")
def get_client(client_id: str, user: dict = Depends(get_current_user)):
    """Get a single client with full profile."""
    res = (
        supabase.table("clients")
        .select("*")
        .eq("id", client_id)
        .eq("nutritionist_id", user["id"])
        .execute()
    )
    data = res.data or []
    if not data:
        raise HTTPException(status_code=404, detail="Client not found")

    client = data[0]

    # Get today's checkin
    today = date.today().isoformat()
    checkin_res = (
        supabase.table("checkins")
        .select("*")
        .eq("client_id", client_id)
        .eq("checkin_date", today)
        .execute()
    )
    today_checkin = checkin_res.data[0] if checkin_res.data else None

    # Get pending queries count
    queries_res = (
        supabase.table("pending_queries")
        .select("id", count="exact")
        .eq("client_id", client_id)
        .eq("status", "pending")
        .execute()
    )
    pending_count = len(queries_res.data) if queries_res.data else 0

    # Generate invite code
    from db.invite_codes import generate_code
    invite_code = generate_code(client_id)

    return {
        "client": client,
        "today_checkin": today_checkin,
        "pending_queries_count": pending_count,
        "invite_code": invite_code,
    }


@router.post("")
def create_client(req: ClientCreate, user: dict = Depends(get_current_user)):
    """Add a new client. Auto-computes program_end."""
    # Compute program end date
    program_start = req.program_start or date.today().isoformat()
    program_end = (
        date.fromisoformat(program_start) + timedelta(days=req.program_duration)
    ).isoformat()

    client_data = {
        "nutritionist_id": user["id"],
        "full_name": req.full_name,
        "telegram_phone": req.telegram_phone,
        "telegram_user_id": req.telegram_user_id,
        "program_type": req.program_type,
        "program_duration": req.program_duration,
        "program_start": program_start,
        "program_end": program_end,
        "checkin_time": req.checkin_time,
        "diet_chart": req.diet_chart,
        "caretaker_name": req.caretaker_name,
        "caretaker_telegram": req.caretaker_telegram,
        "status": "active",
    }

    res = supabase.table("clients").insert(client_data).execute()
    client = res.data[0]

    # Generate invite code
    from db.invite_codes import generate_code
    invite_code = generate_code(client["id"])

    return {
        "client": client,
        "invite_code": invite_code,
        "message": "Client created successfully"
    }


@router.patch("/{client_id}")
def update_client(
    client_id: str,
    req: ClientUpdate,
    user: dict = Depends(get_current_user),
):
    """Update client info. Only updates fields that are provided."""
    # Verify ownership
    check = (
        supabase.table("clients")
        .select("id")
        .eq("id", client_id)
        .eq("nutritionist_id", user["id"])
        .execute()
    )
    if not check.data:
        raise HTTPException(status_code=404, detail="Client not found")

    # Build update dict (only non-None fields)
    update_data = {k: v for k, v in req.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Recompute program_end if duration or start changed
    if "program_duration" in update_data or "program_start" in update_data:
        current = supabase.table("clients").select("*").eq("id", client_id).execute().data[0]
        start = update_data.get("program_start", current.get("program_start"))
        duration = update_data.get("program_duration", current.get("program_duration"))
        update_data["program_end"] = (
            date.fromisoformat(start) + timedelta(days=duration)
        ).isoformat()

    res = (
        supabase.table("clients")
        .update(update_data)
        .eq("id", client_id)
        .execute()
    )

    return {"client": res.data[0], "message": "Client updated"}


@router.delete("/{client_id}")
def delete_client(client_id: str, user: dict = Depends(get_current_user)):
    """Actually delete a client and all their data."""
    check = (
        supabase.table("clients")
        .select("id")
        .eq("id", client_id)
        .eq("nutritionist_id", user["id"])
        .execute()
    )
    if not check.data:
        raise HTTPException(status_code=404, detail="Client not found")

    # Delete related data first (due to foreign key constraints)
    supabase.table("checkins").delete().eq("client_id", client_id).execute()
    supabase.table("messages").delete().eq("client_id", client_id).execute()
    supabase.table("pending_queries").delete().eq("client_id", client_id).execute()
    supabase.table("ai_rules").delete().eq("client_id", client_id).execute()

    # Delete the client
    supabase.table("clients").delete().eq("id", client_id).execute()

    return {"message": "Client deleted"}
