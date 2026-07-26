"""
api/routes/rules.py
-------------------
AI Rules endpoints:
GET    /rules                — Get master rules for this nutritionist
GET    /clients/:id/rules    — Get client-specific rules
POST   /rules                — Add master rule
POST   /clients/:id/rules    — Add client-specific rule
DELETE /rules/:id            — Remove a rule
PATCH  /rules/:id            — Toggle rule active/inactive
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from api.middleware import get_current_user
from db.client import supabase

router = APIRouter()


# ── Request models ───────────────────────────────────────────────────────────

class RuleCreate(BaseModel):
    category: str  # 'tone', 'language', 'medical', 'caretaker', 'other'
    rule_text: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("")
def get_master_rules(user: dict = Depends(get_current_user)):
    """Get all master rules for this nutritionist (applies to all clients)."""
    res = (
        supabase.table("ai_rules")
        .select("*")
        .eq("nutritionist_id", user["id"])
        .is_("client_id", "null")
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


@router.get("/client/{client_id}")
def get_client_rules(client_id: str, user: dict = Depends(get_current_user)):
    """Get rules specific to a client."""
    # Verify client ownership
    check = (
        supabase.table("clients")
        .select("id")
        .eq("id", client_id)
        .eq("nutritionist_id", user["id"])
        .execute()
    )
    if not check.data:
        raise HTTPException(status_code=404, detail="Client not found")

    res = (
        supabase.table("ai_rules")
        .select("*")
        .eq("client_id", client_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


@router.post("")
def create_master_rule(req: RuleCreate, user: dict = Depends(get_current_user)):
    """Add a master rule (applies to all clients)."""
    rule_data = {
        "nutritionist_id": user["id"],
        "client_id": None,
        "category": req.category,
        "rule_text": req.rule_text,
        "is_active": True,
    }
    res = supabase.table("ai_rules").insert(rule_data).execute()
    return {"rule": res.data[0], "message": "Master rule created"}


@router.post("/client/{client_id}")
def create_client_rule(
    client_id: str,
    req: RuleCreate,
    user: dict = Depends(get_current_user),
):
    """Add a rule specific to one client."""
    # Verify client ownership
    check = (
        supabase.table("clients")
        .select("id")
        .eq("id", client_id)
        .eq("nutritionist_id", user["id"])
        .execute()
    )
    if not check.data:
        raise HTTPException(status_code=404, detail="Client not found")

    rule_data = {
        "nutritionist_id": user["id"],
        "client_id": client_id,
        "category": req.category,
        "rule_text": req.rule_text,
        "is_active": True,
    }
    res = supabase.table("ai_rules").insert(rule_data).execute()
    return {"rule": res.data[0], "message": "Client rule created"}


@router.delete("/{rule_id}")
def delete_rule(rule_id: str, user: dict = Depends(get_current_user)):
    """Delete a rule."""
    check = (
        supabase.table("ai_rules")
        .select("id")
        .eq("id", rule_id)
        .eq("nutritionist_id", user["id"])
        .execute()
    )
    if not check.data:
        raise HTTPException(status_code=404, detail="Rule not found")

    supabase.table("ai_rules").delete().eq("id", rule_id).execute()
    return {"message": "Rule deleted"}


@router.patch("/{rule_id}/toggle")
def toggle_rule(rule_id: str, user: dict = Depends(get_current_user)):
    """Toggle a rule active/inactive."""
    check = (
        supabase.table("ai_rules")
        .select("*")
        .eq("id", rule_id)
        .eq("nutritionist_id", user["id"])
        .execute()
    )
    if not check.data:
        raise HTTPException(status_code=404, detail="Rule not found")

    rule = check.data[0]
    new_status = not rule.get("is_active", True)

    supabase.table("ai_rules").update({"is_active": new_status}).eq("id", rule_id).execute()

    return {"message": f"Rule {'activated' if new_status else 'deactivated'}"}
