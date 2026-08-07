"""
bot/handlers/message_handler.py
--------------------------------
Handles ALL incoming text messages in any Telegram group.
Identifies sender role and routes accordingly.
"""

from telegram import Update
from telegram.ext import ContextTypes

from logger import get_logger
logger = get_logger("bot.message_handler")

import db.clients as db_clients
import db.nutritionists as db_nutritionists
import db.messages as db_messages
import db.queries as db_queries
import db.checkins as db_checkins
from ai.router import route


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Entry point for every group message.
    Only responds to CLIENT messages. Ignores nutritionist and caretaker.
    """
    msg = update.message
    if not msg or not msg.text:
        return

    group_id = msg.chat.id
    sender_id = msg.from_user.id
    sender_name = msg.from_user.full_name
    message_text = msg.text.strip()
    telegram_msg_id = msg.message_id

    # Ignore bots
    if msg.from_user.is_bot:
        return

    # Find the client for this group
    try:
        client = db_clients.get_by_group_id(group_id)
    except Exception as e:
        logger.error(f"DB error in get_by_group_id: {e}")
        return
    if not client:
        return

    client_id = client["id"]
    nutritionist = db_nutritionists.get_by_id(client["nutritionist_id"])
    is_sender_nutritionist = (nutritionist and sender_id == nutritionist.get("telegram_user_id"))
    is_sender_caretaker = (sender_id == client.get("caretaker_telegram"))
    is_sender_client = (sender_id == client.get("telegram_user_id"))

    # ── NUTRITIONIST: Just log the message, don't respond ──────────────────
    if is_sender_nutritionist:
        db_messages.save(
            client_id=client_id,
            sender_role="nutritionist",
            content=message_text,
            sender_name=sender_name,
            telegram_msg_id=telegram_msg_id,
        )
        # Auto-resolve any open query
        resolved_query = db_queries.auto_resolve_on_doctor_message(client_id, message_text)
        if resolved_query:
            # Notify doctor in DM that a query was auto-resolved
            try:
                await context.bot.send_message(
                    chat_id=sender_id,
                    text=f"Resolved query for {client['full_name']}: \"{resolved_query.get('client_message', '')[:100]}\"",
                )
            except Exception as e:
                logger.error(f"Failed to send auto-resolve notification: {e}")
        return

    # ── CARETAKER: Log and respond with AI ─────────────────────────────────
    if is_sender_caretaker:
        db_messages.save(
            client_id=client_id,
            sender_role="caretaker",
            content=message_text,
            sender_name=sender_name,
            telegram_msg_id=telegram_msg_id,
        )
        db_checkins.update_today(client_id=client_id, caretaker_note=message_text)

        # Don't respond if paused
        if client.get("status") == "paused":
            return

        # Show typing indicator
        await context.bot.send_chat_action(chat_id=group_id, action="typing")

        # Call AI router
        try:
            result = route(
                client_id=client_id,
                message_text=message_text,
                telegram_msg_id=telegram_msg_id,
                sender_role="caretaker",
            )
        except Exception as e:
            logger.error(f"AI router error for caretaker message: {e}")
            return

        # Send AI reply
        await msg.reply_text(result["reply"])
        return

    # ── CLIENT: Process with AI and respond ───────────────────────────────
    if is_sender_client:
        # Don't respond if paused
        if client.get("status") == "paused":
            await msg.reply_text("Your program is currently on pause. Contact your doctor to resume.")
            return

        # Show typing indicator
        await context.bot.send_chat_action(chat_id=group_id, action="typing")

        # Call AI router
        try:
            result = route(
                client_id=client_id,
                message_text=message_text,
                telegram_msg_id=telegram_msg_id,
                sender_role="client",
            )
        except Exception as e:
            logger.error(f"AI router error for client message: {e}")
            await msg.reply_text("Sorry, I'm having trouble processing that right now. Please try again.")
            return

        # Send AI reply
        await msg.reply_text(result["reply"])

        # If escalated, notify nutritionist
        if result["action"] == "escalate" and result.get("nutritionist_telegram_id"):
            try:
                await context.bot.send_message(
                    chat_id=result["nutritionist_telegram_id"],
                    text=f"Pending Query — {result['client_name']}\n\nClient asked: {message_text}\n\nPlease review in the group.",
                )
            except Exception as e:
                logger.error(f"Failed to send escalation notification: {e}")
