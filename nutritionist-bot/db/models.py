"""
db/models.py — SQLAlchemy ORM models for the nutrition bot.

Tables:
  - clients   : one row per client group
  - messages  : raw conversation log (every message from every person + bot)
  - checkins  : structured data extracted from each check-in response
"""

from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, DateTime,
    ForeignKey, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Client(Base):
    """
    One row per client. telegram_group_id is the unique key that links
    incoming Telegram messages to the right client record.
    """
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True)

    name = Column(String(200), nullable=False)

    # Telegram group chat ID (negative integer, stored as string for safety)
    telegram_group_id = Column(String(50), nullable=False, unique=True)

    # Telegram user IDs of the three humans in the group
    customer_telegram_id = Column(String(50), nullable=True)
    caretaker_telegram_id = Column(String(50), nullable=True)
    nutritionist_telegram_id = Column(String(50), nullable=True)

    # Full diet/nutrition plan for this client — injected into every AI prompt
    plan_summary = Column(Text, nullable=False)

    # Special coaching instructions / rules specific to this client
    custom_instructions = Column(Text, nullable=True)

    # Set to 'daily' or 'weekly' when a check-in question has been sent;
    # cleared back to NULL after the client/caretaker replies.
    pending_checkin_type = Column(String(10), nullable=True)

    subscription_start = Column(Date, default=date.today)
    active = Column(Boolean, default=True, nullable=False)

    # Relationships
    messages = relationship("Message", back_populates="client", cascade="all, delete-orphan")
    checkins = relationship("CheckIn", back_populates="client", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Client id={self.id} name={self.name!r} group={self.telegram_group_id}>"


class Message(Base):
    """
    Raw conversation log. Every single message — from the bot, the client,
    the caretaker, and the nutritionist — is saved here.
    This is what gives the AI full conversation continuity per client.
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)

    # 'customer' | 'caretaker' | 'nutritionist' | 'bot'
    sender_role = Column(String(20), nullable=False)

    sender_telegram_id = Column(String(50), nullable=True)
    message_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    client = relationship("Client", back_populates="messages")

    def __repr__(self):
        return f"<Message id={self.id} role={self.sender_role!r} client={self.client_id}>"


class CheckIn(Base):
    """
    Structured data extracted by Gemini from each client's check-in reply.
    This is the clean, queryable record the nutritionist actually tracks over time.
    """
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)

    # 'daily' | 'weekly'
    type = Column(String(10), nullable=False)

    # Raw reply text that triggered this check-in record
    raw_reply = Column(Text, nullable=True)

    # Structured fields extracted by Gemini
    adherence = Column(String(20), nullable=True)       # on_track | partial | off_track | unclear
    energy_level = Column(String(20), nullable=True)    # low | medium | high | not_mentioned
    mood = Column(String(200), nullable=True)
    symptoms = Column(Text, nullable=True)              # JSON array stored as string
    caretaker_note = Column(Text, nullable=True)

    # Flag for nutritionist attention
    needs_attention = Column(Boolean, default=False, nullable=False)
    flag_reason = Column(Text, nullable=True)

    # One-line summary for the nutritionist's records
    summary = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    client = relationship("Client", back_populates="checkins")

    def __repr__(self):
        return (
            f"<CheckIn id={self.id} type={self.type!r} "
            f"adherence={self.adherence!r} flag={self.needs_attention}>"
        )
