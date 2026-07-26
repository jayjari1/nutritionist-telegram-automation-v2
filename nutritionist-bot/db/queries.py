"""
db/queries.py — All database query helpers.

Keep all SQL/ORM logic here so handlers and the AI layer stay clean.
"""

import json
from typing import Optional
from sqlalchemy.orm import Session

from db.models import Client, Message, CheckIn
import config


# ── Client helpers ────────────────────────────────────────────────────────────

def get_client_by_group(session: Session, telegram_group_id: str) -> Optional[Client]:
    """Return the Client whose telegram_group_id matches, or None."""
    return (
        session.query(Client)
        .filter(Client.telegram_group_id == str(telegram_group_id))
        .first()
    )


def get_all_active_clients(session: Session) -> list[Client]:
    """Return all active clients (used by the scheduler)."""
    return session.query(Client).filter(Client.active == True).all()


def set_pending_checkin(session: Session, client: Client, checkin_type: str) -> None:
    """Mark that a check-in question has been sent for this client."""
    client.pending_checkin_type = checkin_type
    session.commit()


def clear_pending_checkin(session: Session, client: Client) -> None:
    """Clear the pending check-in after a reply has been processed."""
    client.pending_checkin_type = None
    session.commit()


def get_client_by_id(session: Session, client_id: int) -> Optional[Client]:
    """Return a client by their internal DB id."""
    return session.query(Client).filter(Client.id == client_id).first()


def update_client_instructions(session: Session, client: Client, instructions: Optional[str]) -> None:
    """Add, update, or clear special coaching instructions for a client."""
    client.custom_instructions = instructions
    session.commit()


# ── Message helpers ───────────────────────────────────────────────────────────

def save_message(
    session: Session,
    client: Client,
    sender_role: str,
    message_text: str,
    sender_telegram_id: Optional[str] = None,
) -> Message:
    """
    Persist a message to the raw conversation log.
    sender_role must be one of: 'customer', 'caretaker', 'nutritionist', 'bot'
    """
    msg = Message(
        client_id=client.id,
        sender_role=sender_role,
        sender_telegram_id=str(sender_telegram_id) if sender_telegram_id else None,
        message_text=message_text,
    )
    session.add(msg)
    session.commit()
    return msg


def get_recent_messages(session: Session, client: Client, limit: int = None) -> list[Message]:
    """
    Return the most recent N messages for a client, ordered oldest → newest.
    These are injected into Gemini as conversation context.
    """
    limit = limit or config.CONTEXT_MESSAGE_LIMIT
    rows = (
        session.query(Message)
        .filter(Message.client_id == client.id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(rows))  # reverse so oldest is first


# ── CheckIn helpers ───────────────────────────────────────────────────────────

def save_checkin(
    session: Session,
    client: Client,
    checkin_type: str,
    raw_reply: str,
    extracted: dict,
) -> CheckIn:
    """
    Persist structured check-in data extracted by Gemini.
    `extracted` is the dict from the JSON extraction call.
    """
    # Safely pull each field from the extracted dict
    symptoms = extracted.get("symptoms", [])
    if isinstance(symptoms, list):
        symptoms = json.dumps(symptoms, ensure_ascii=False)

    checkin = CheckIn(
        client_id=client.id,
        type=checkin_type,
        raw_reply=raw_reply,
        adherence=extracted.get("adherence"),
        energy_level=extracted.get("energy_level"),
        mood=extracted.get("mood"),
        symptoms=symptoms,
        caretaker_note=extracted.get("caretaker_note"),
        needs_attention=bool(extracted.get("needs_attention", False)),
        flag_reason=extracted.get("flag_reason"),
        summary=extracted.get("summary"),
    )
    session.add(checkin)
    session.commit()
    return checkin


def get_recent_checkins(session: Session, client: Client, limit: int = 7) -> list[CheckIn]:
    """Return recent check-ins for a client (newest first), used for weekly summaries."""
    return (
        session.query(CheckIn)
        .filter(CheckIn.client_id == client.id)
        .order_by(CheckIn.created_at.desc())
        .limit(limit)
        .all()
    )


def get_all_clients_count(session: Session) -> int:
    """Total number of clients (active + inactive)."""
    return session.query(Client).count()


def add_client(
    session: Session,
    name: str,
    telegram_group_id: str,
    plan_summary: str,
    customer_telegram_id: str = None,
    caretaker_telegram_id: str = None,
    nutritionist_telegram_id: str = None,
) -> Client:
    """Insert a new client row."""
    client = Client(
        name=name,
        telegram_group_id=telegram_group_id,
        plan_summary=plan_summary,
        customer_telegram_id=customer_telegram_id,
        caretaker_telegram_id=caretaker_telegram_id,
        nutritionist_telegram_id=nutritionist_telegram_id,
    )
    session.add(client)
    session.commit()
    return client
