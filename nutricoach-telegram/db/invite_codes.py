"""
db/invite_codes.py
------------------
Generate and manage unique invite codes for clients.
Code format: NC-{FIRST4CHARS_OF_ID}
Example: NC-A3F2
"""

from typing import Optional
from db.client import supabase


def generate_code(client_id: str) -> str:
    """Generate a short invite code from client ID."""
    # Take first 8 chars of UUID, uppercase, add NC prefix
    short = client_id.replace("-", "")[:8].upper()
    return f"NC-{short}"


def find_by_code(code: str) -> Optional[dict]:
    """Find a client by their invite code."""
    # Get all clients and check codes
    # (In production, you'd store the code in a column)
    code = code.strip().upper()
    if not code.startswith("NC-"):
        return None

    # Extract the ID portion
    id_part = code[3:]  # Remove "NC-" prefix

    # Query all clients and match
    res = supabase.table("clients").select("*").execute()
    for client in (res.data or []):
        client_code = generate_code(client["id"])
        if client_code == code:
            return client

    return None
