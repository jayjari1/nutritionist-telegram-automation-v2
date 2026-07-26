"""
db/messages.py
--------------
All database operations for the messages table.
Stores every message in every client's Telegram group.
This is what the web app reads to show the chat history.
"""

from db.client import supabase
from typing import Optional


def save(
    client_id: str,
    sender_role: str,
    content: str,
    sender_name: Optional[str] = None,
    telegram_msg_id: Optional[int] = None,
) -> dict:
    """
    Save any message to the database.
    sender_role: 'client', 'ai', 'nutritionist', 'caretaker', 'system'
    """
    res = supabase.table("messages").insert({
        "client_id": client_id,
        "sender_role": sender_role,
        "sender_name": sender_name,
        "content": content,
        "telegram_msg_id": telegram_msg_id,
    }).execute()
    return res.data[0]


def get_recent(client_id: str, limit: int = 10) -> list:
    """
    Get the last N messages for a client.
    Used by AI as conversation context (so it remembers what was said).
    """
    res = (
        supabase.table("messages")
        .select("*")
        .eq("client_id", client_id)
        .order("sent_at", desc=True)
        .limit(limit)
        .execute()
    )
    # Reverse so oldest is first (chronological order for AI context)
    return list(reversed(res.data or []))


def get_all(client_id: str, offset: int = 0, limit: int = 50) -> list:
    """
    Get paginated messages for a client.
    Used by web app to show full chat history.
    """
    res = (
        supabase.table("messages")
        .select("*")
        .eq("client_id", client_id)
        .order("sent_at", desc=False)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return res.data or []


def format_for_ai_context(messages: list) -> str:
    """
    Formats message history into a readable string for the AI prompt.
    Example: "[Client] Had breakfast properly today\\n[AI] Great work! ..."
    """
    lines = []
    role_labels = {
        "client": "Client",
        "ai": "AI",
        "nutritionist": "Doctor",
        "caretaker": "Caretaker",
        "system": "System",
    }
    for msg in messages:
        role = role_labels.get(msg["sender_role"], "Unknown")
        lines.append(f"[{role}]: {msg['content']}")
    return "\n".join(lines)
