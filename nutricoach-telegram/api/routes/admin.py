"""
api/routes/admin.py
-------------------
Admin endpoints:
GET  /admin/nutritionists              — Get all nutritionists
PATCH /admin/nutritionists/:id/approve — Approve pending nutritionist
PATCH /admin/nutritionists/:id/pause   — Pause nutritionist
PATCH /admin/nutritionists/:id/reactivate — Reactivate paused nutritionist
GET  /admin/stats                      — Platform-wide stats
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from api.middleware import require_admin
from db.client import supabase

router = APIRouter()


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/nutritionists")
def get_all_nutritionists(user: dict = Depends(require_admin)):
    """Get all nutritionists across the platform."""
    res = (
        supabase.table("nutritionists")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


@router.patch("/nutritionists/{nutritionist_id}/approve")
def approve_nutritionist(nutritionist_id: str, user: dict = Depends(require_admin)):
    """Approve a pending nutritionist."""
    from datetime import datetime, timezone

    existing = (
        supabase.table("nutritionists")
        .select("*")
        .eq("id", nutritionist_id)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Nutritionist not found")

    nut = existing.data[0]
    if nut["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot approve — status is {nut['status']}")

    supabase.table("nutritionists").update({
        "status": "active",
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "approved_by": user["id"],
    }).eq("id", nutritionist_id).execute()

    return {"message": f"{nut['full_name']} approved"}


@router.patch("/nutritionists/{nutritionist_id}/pause")
def pause_nutritionist(nutritionist_id: str, user: dict = Depends(require_admin)):
    """Pause a nutritionist — bot stops for all their clients."""
    existing = (
        supabase.table("nutritionists")
        .select("*")
        .eq("id", nutritionist_id)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Nutritionist not found")

    nut = existing.data[0]
    if nut["status"] == "paused":
        raise HTTPException(status_code=400, detail="Already paused")

    supabase.table("nutritionists").update({"status": "paused"}).eq("id", nutritionist_id).execute()

    return {"message": f"{nut['full_name']} paused"}


@router.patch("/nutritionists/{nutritionist_id}/reactivate")
def reactivate_nutritionist(nutritionist_id: str, user: dict = Depends(require_admin)):
    """Reactivate a paused nutritionist."""
    existing = (
        supabase.table("nutritionists")
        .select("*")
        .eq("id", nutritionist_id)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Nutritionist not found")

    nut = existing.data[0]
    if nut["status"] == "active":
        raise HTTPException(status_code=400, detail="Already active")

    supabase.table("nutritionists").update({"status": "active"}).eq("id", nutritionist_id).execute()

    return {"message": f"{nut['full_name']} reactivated"}


@router.get("/stats")
def get_platform_stats(user: dict = Depends(require_admin)):
    """Get platform-wide statistics."""
    # Count nutritionists by status
    nuts = supabase.table("nutritionists").select("status").execute()
    nut_statuses = {}
    for n in (nuts.data or []):
        s = n["status"]
        nut_statuses[s] = nut_statuses.get(s, 0) + 1

    # Count clients by status
    clients = supabase.table("clients").select("status").execute()
    client_statuses = {}
    for c in (clients.data or []):
        s = c["status"]
        client_statuses[s] = client_statuses.get(s, 0) + 1

    # Pending queries
    pending = (
        supabase.table("pending_queries")
        .select("id", count="exact")
        .eq("status", "pending")
        .execute()
    )
    pending_count = len(pending.data) if pending.data else 0

    return {
        "nutritionists": nut_statuses,
        "clients": client_statuses,
        "total_nutritionists": sum(nut_statuses.values()),
        "total_clients": sum(client_statuses.values()),
        "pending_queries": pending_count,
    }
