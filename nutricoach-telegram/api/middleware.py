"""
api/middleware.py
----------------
FastAPI dependencies for protecting routes.
Usage: Add `user = Depends(get_current_user)` to any route.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from api.auth import decode_token
from db.client import supabase

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Extract and verify JWT token from Authorization header.
    Returns the user record from the database.
    """
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    role = payload.get("role")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Fetch user from database based on role
    if role == "admin":
        res = supabase.table("admins").select("*").eq("id", user_id).execute()
    else:
        res = supabase.table("nutritionists").select("*").eq("id", user_id).execute()

    data = res.data or []
    if not data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    user = data[0]

    # Check if nutritionist is active
    if role != "admin" and user.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.get('status')}. Contact admin.",
        )

    # Attach role to user dict
    user["_role"] = role
    return user


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Only allow admin users."""
    if user.get("_role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
