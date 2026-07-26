"""
api/routes/config.py
--------------------
Admin config endpoints:
GET    /config           — Get all config (secrets masked)
GET    /config/raw       — Get all config (secrets visible, admin only)
POST   /config           — Create/update config entry
DELETE /config/:key      — Delete config entry
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from api.middleware import require_admin
from db.client import supabase

router = APIRouter()


class ConfigUpdate(BaseModel):
    key: str
    value: str
    category: Optional[str] = "general"
    description: Optional[str] = ""
    is_secret: Optional[bool] = False


def _mask_value(entry: dict) -> dict:
    """Mask secret values for safe display."""
    result = dict(entry)
    if result.get("is_secret") and result.get("value"):
        val = result["value"]
        if len(val) > 8:
            result["value"] = val[:4] + "*" * (len(val) - 8) + val[-4:]
        else:
            result["value"] = "****"
    return result


@router.get("")
def get_all_config(user: dict = Depends(require_admin)):
    """Get all config entries (secrets masked)."""
    res = supabase.table("app_config").select("*").order("category").execute()
    entries = res.data or []
    return [_mask_value(e) for e in entries]


@router.get("/raw")
def get_raw_config(user: dict = Depends(require_admin)):
    """Get all config entries (secrets visible). Admin only."""
    res = supabase.table("app_config").select("*").order("category").execute()
    return res.data or []


@router.post("")
def upsert_config(req: ConfigUpdate, user: dict = Depends(require_admin)):
    """Create or update a config entry."""
    from datetime import datetime, timezone
    res = supabase.table("app_config").upsert({
        "key": req.key,
        "value": req.value,
        "category": req.category,
        "description": req.description,
        "is_secret": req.is_secret,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    return {"message": f"Config '{req.key}' updated", "entry": res.data[0] if res.data else {}}


@router.delete("/{key}")
def delete_config(key: str, user: dict = Depends(require_admin)):
    """Delete a config entry."""
    supabase.table("app_config").delete().eq("key", key).execute()
    return {"message": f"Config '{key}' deleted"}


@router.post("/sync-env")
def sync_from_env(user: dict = Depends(require_admin)):
    """Sync config values from .env file to database."""
    import os
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    env_keys = [
        ("TELEGRAM_BOT_TOKEN", "telegram", "Telegram Bot API Token", True),
        ("TELEGRAM_BOT_USERNAME", "telegram", "Bot username", False),
        ("SUPABASE_URL", "supabase", "Supabase project URL", True),
        ("SUPABASE_ANON_KEY", "supabase", "Supabase anonymous key", True),
        ("SUPABASE_SERVICE_KEY", "supabase", "Supabase service role key", True),
        ("GEMINI_API_KEY", "ai", "Google Gemini API key", True),
        ("GEMINI_MODEL", "ai", "Gemini model name", False),
        ("JWT_SECRET", "auth", "JWT signing secret", True),
        ("JWT_EXPIRY_HOURS", "auth", "Token expiry in hours", False),
        ("ADMIN_EMAIL", "admin", "Admin login email", False),
        ("ADMIN_PASSWORD_HASH", "admin", "Admin password hash", True),
        ("APP_ENV", "general", "Environment", False),
        ("WEBHOOK_URL", "general", "Production webhook URL", False),
        ("PORT", "general", "API server port", False),
    ]
    
    synced = 0
    for key, cat, desc, secret in env_keys:
        val = os.getenv(key, "")
        if val:
            supabase.table("app_config").upsert({
                "key": key, "value": val, "category": cat,
                "description": desc, "is_secret": secret,
            }).execute()
            synced += 1
    
    return {"message": f"Synced {synced} values from .env"}
