"""
bot/handlers.py — Telegram message handlers.

Core logic:
  1. Every text message in a known group is intercepted.
  2. The sender's role is determined (customer / caretaker / nutritionist / unknown).
  3. The message is saved to the DB (full conversation log).
  4. If the sender is the NUTRITIONIST → save, do NOT reply (she's speaking directly).
  5. Otherwise → run AI reply + structured extraction, post reply, save check-in.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

import config
from db.database import get_session
from db.queries import (
    get_client_by_group,
    save_message,
    get_recent_messages,
    save_checkin,
    clear_pending_checkin,
)
from ai.gemini import generate_reply, extract_checkin

logger = logging.getLogger(__name__)


def _determine_sender_role(client, sender_id: str) -> str:
    """
    Map a Telegram user ID to their role in this client's group.
    Returns: 'customer' | 'caretaker' | 'nutritionist' | 'unknown'
    """
    sid = str(sender_id)
    if sid == str(config.COACH_TELEGRAM_ID):
        return "nutritionist"
    if client.customer_telegram_id and sid == str(client.customer_telegram_id):
        return "customer"
    if client.caretaker_telegram_id and sid == str(client.caretaker_telegram_id):
        return "caretaker"
    # Fallback: if IDs not set yet, treat unrecognised non-coach users as customer
    return "customer"


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Main handler for text messages in group chats.
    Registered for: filters.TEXT & ~filters.COMMAND in group/supergroup chats.
    """
    # Only handle text messages in groups
    if not update.message or not update.message.text:
        return

    chat_id = str(update.effective_chat.id)
    sender_id = str(update.effective_user.id)
    message_text = update.message.text.strip()

    with get_session() as session:
        # ── Step 1: Find client by group ID ───────────────────────────────────
        client = get_client_by_group(session, chat_id)
        if not client:
            # This bot is in a group we don't know about
            logger.warning(
                f"⚠️ [HANDLER] Message received from UNKNOWN group! Chat ID is: {chat_id}\n"
                f"   👉 To register it, DM me: /addclient {chat_id} ClientName | Plan Summary"
            )
            return

        # ── Step 2: Determine sender role ─────────────────────────────────────
        sender_role = _determine_sender_role(client, sender_id)

        logger.info(
            f"[HANDLER] Group={chat_id} Client={client.name!r} "
            f"Role={sender_role} Text={message_text[:60]!r}"
        )

        # ── Step 3: Save the incoming message ─────────────────────────────────
        save_message(
            session=session,
            client=client,
            sender_role=sender_role,
            message_text=message_text,
            sender_telegram_id=sender_id,
        )

        # ── Step 4: Nutritionist override — save & stay silent ────────────────
        if sender_role == "nutritionist":
            logger.info(
                f"[HANDLER] Nutritionist spoke in group for '{client.name}' — "
                "saved to DB, bot staying silent."
            )
            return

        # ── Step 5: Ignore unknown roles that might be random group admins etc.
        # In practice 'unknown' falls back to 'customer' in _determine_sender_role,
        # but leave this guard here for safety.
        if sender_role not in ("customer", "caretaker"):
            return

        # ── Step 6: Get conversation history for AI context ───────────────────
        recent_messages = get_recent_messages(session, client)

        # ── Step 7: Generate natural-language reply ───────────────────────────
        try:
            reply_text = generate_reply(
                client=client,
                recent_messages=recent_messages,
                new_message=message_text,
                sender_role=sender_role,
            )
        except Exception as e:
            logger.error(f"[HANDLER] Reply generation failed for '{client.name}': {e}")
            # Don't crash — send a safe fallback so the group isn't left hanging
            reply_text = (
                "Thanks for the update! I'll make sure to note this. "
                f"Feel free to reach out to {config.COACH_NAME} if you need anything."
            )

        # ── Step 8: Post reply to Telegram group ──────────────────────────────
        await context.bot.send_message(chat_id=chat_id, text=reply_text)

        # ── Step 9: Save bot's reply to the message log ───────────────────────
        save_message(
            session=session,
            client=client,
            sender_role="bot",
            message_text=reply_text,
        )

        # ── Step 10: Extract structured check-in data ─────────────────────────
        checkin_type = client.pending_checkin_type  # may be None

        try:
            extracted = extract_checkin(
                client=client,
                recent_messages=recent_messages,
                new_message=message_text,
                sender_role=sender_role,
            )
        except Exception as e:
            logger.error(f"[HANDLER] Extraction failed for '{client.name}': {e}")
            extracted = None

        if extracted:
            # ── Step 11: Save check-in record ─────────────────────────────────
            checkin = save_checkin(
                session=session,
                client=client,
                checkin_type=checkin_type or "daily",
                raw_reply=message_text,
                extracted=extracted,
            )

            # ── Step 12: Clear pending check-in flag ──────────────────────────
            if checkin_type:
                clear_pending_checkin(session, client)

            # ── Step 13: Flag for attention ───────────────────────────────────
            if extracted.get("needs_attention"):
                reason = extracted.get("flag_reason", "No reason given")
                logger.warning(
                    f"\n{'='*60}\n"
                    f"[FLAG] ⚠️  Client '{client.name}' needs attention!\n"
                    f"  Reason: {reason}\n"
                    f"  Summary: {extracted.get('summary', 'N/A')}\n"
                    f"  Group: {chat_id}\n"
                    f"{'='*60}\n"
                    # TODO (production): DM the coach, send to dashboard, or trigger an alert
                )
