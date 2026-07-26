"""
api/routes/auth.py
------------------
Authentication endpoints:
POST /auth/login      — Nutritionist login
POST /auth/signup     — New nutritionist registration
POST /auth/admin/login — Admin login
GET  /auth/me         — Get current logged-in user
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional

from api.auth import hash_password, verify_password, create_token
from api.middleware import get_current_user
from db.client import supabase

router = APIRouter()


# ── Request models ───────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    full_name: str
    email: str
    password: str
    clinic_name: Optional[str] = None
    telegram_user_id: Optional[int] = None


class AdminLoginRequest(BaseModel):
    email: str
    password: str


# ── Nutritionist Auth ────────────────────────────────────────────────────────

@router.post("/login")
def login(req: LoginRequest):
    """Nutritionist login — returns JWT token."""
    res = supabase.table("nutritionists").select("*").eq("email", req.email).execute()
    data = res.data or []

    if not data:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user = data[0]

    if not verify_password(req.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if user["status"] == "pending":
        raise HTTPException(status_code=403, detail="Account pending admin approval")
    if user["status"] == "expired":
        raise HTTPException(status_code=403, detail="Account expired. Contact admin.")
    if user["status"] == "paused":
        raise HTTPException(status_code=403, detail="Account paused. Contact admin.")

    token = create_token(user["id"], role="nutritionist")

    return {
        "token": token,
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "clinic_name": user.get("clinic_name"),
            "status": user["status"],
        },
    }


@router.post("/signup")
def signup(req: SignupRequest):
    """New nutritionist registration — status = pending until admin approves."""
    # Check if email already exists
    existing = supabase.table("nutritionists").select("id").eq("email", req.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create nutritionist
    new_user = {
        "full_name": req.full_name,
        "email": req.email,
        "password": hash_password(req.password),
        "clinic_name": req.clinic_name,
        "telegram_user_id": req.telegram_user_id,
        "status": "pending",
    }

    res = supabase.table("nutritionists").insert(new_user).execute()
    user = res.data[0]

    return {
        "message": "Registration successful. Waiting for admin approval.",
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "status": user["status"],
        },
    }


# ── Admin Auth ───────────────────────────────────────────────────────────────

@router.post("/admin/login")
def admin_login(req: AdminLoginRequest):
    """Admin login — separate from nutritionist login."""
    from config import ADMIN_EMAIL, ADMIN_PASSWORD_HASH

    if req.email != ADMIN_EMAIL:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # For admin, we accept plain password check if no hash is set
    if ADMIN_PASSWORD_HASH:
        if not verify_password(req.password, ADMIN_PASSWORD_HASH):
            raise HTTPException(status_code=401, detail="Invalid credentials")
    else:
        # Dev mode: accept any password for admin
        pass

    # Get or create admin record
    existing = supabase.table("admins").select("*").eq("email", req.email).execute()
    if existing.data:
        admin_id = existing.data[0]["id"]
    else:
        res = supabase.table("admins").insert({
            "email": req.email,
            "password": hash_password(req.password),
        }).execute()
        admin_id = res.data[0]["id"]

    token = create_token(admin_id, role="admin")

    return {
        "token": token,
        "user": {
            "id": admin_id,
            "email": req.email,
            "role": "admin",
        },
    }


# ── Current User ─────────────────────────────────────────────────────────────

@router.get("/me")
def get_me(user: dict = Depends(get_current_user)):
    """Get the currently logged-in user's profile."""
    return {
        "id": user["id"],
        "full_name": user.get("full_name"),
        "email": user.get("email"),
        "clinic_name": user.get("clinic_name"),
        "status": user.get("status"),
        "role": user.get("_role"),
    }
