"""
bot/commands.py — Telegram slash commands (nutritionist-only).

Commands:
  /testdaily  — Fire a daily check-in right now (for demo/testing)
  /testweekly — Fire a weekly check-in right now (for demo/testing)
  /status     — Show bot status: active clients, last check-in times
  /addclient  — Add a new client (interactive prompt)
  /help       — Show available commands
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

import config
from db.database import get_session
from db.queries import (
    get_all_active_clients,
    get_client_by_group,
    get_recent_messages,
    get_recent_checkins,
    save_message,
    set_pending_checkin,
    add_client,
    update_client_instructions,
)
from ai.gemini import generate_checkin_question

logger = logging.getLogger(__name__)


def _is_coach(update: Update) -> bool:
    """Check if the sender is the nutritionist (coach)."""
    return update.effective_user.id == config.COACH_TELEGRAM_ID


def _coach_only(func):
    """Decorator: silently ignore command if not sent by the coach."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _is_coach(update):
            await update.message.reply_text("❌ This command is only for the nutritionist.")
            return
        return await func(update, context)
    return wrapper


# ── /start & /help ────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — basic greeting."""
    if _is_coach(update):
        await update.message.reply_text(
            f"👋 Hello {config.COACH_NAME}!\n\n"
            "I'm your nutrition accountability bot. Here are your commands:\n\n"
            "• /testdaily — Send a daily check-in to ALL active groups now\n"
            "• /testweekly — Send a weekly check-in to ALL active groups now\n"
            "• /status — View active clients and bot status\n"
            "• /addclient — Add a new client\n"
            "• /note — Add custom AI coaching rules for a client\n"
            "• /help — Show this message"
        )
    else:
        await update.message.reply_text(
            "👋 Hello! I'm a nutrition accountability assistant. "
            "I'll check in with you about your diet plan every day. "
            "Just reply to my messages and I'll keep track of your progress! 🥗"
        )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await cmd_start(update, context)


async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the chat ID of the current chat or group."""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    await update.message.reply_text(
        f"📍 Current Chat Info:\n"
        f"• Chat ID: {chat_id}\n"
        f"• Type: {chat_type}\n\n"
        f"💡 To register this group, copy the Chat ID above and DM me:\n"
        f"/addclient {chat_id} ClientName | Diet Plan Summary"
    )


# ── /status ───────────────────────────────────────────────────────────────────

@_coach_only
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show active clients and their last check-in."""
    with get_session() as session:
        clients = get_all_active_clients(session)
        if not clients:
            await update.message.reply_text("No active clients found. Use /addclient to add one.")
            return

        lines = [f"📊 *Bot Status* — {len(clients)} active client(s)\n"]
        for c in clients:
            checkins = get_recent_checkins(session, c, limit=1)
            last_ci = checkins[0].created_at.strftime("%d %b %Y %H:%M") if checkins else "Never"
            pending = c.pending_checkin_type or "None"
            lines.append(
                f"• *{c.name}*\n"
                f"  Last check-in: {last_ci}\n"
                f"  Pending: {pending}\n"
                f"  Group ID: {c.telegram_group_id}\n"
                f"  Rules: {c.custom_instructions[:40] + '...' if c.custom_instructions and len(c.custom_instructions) > 40 else (c.custom_instructions or 'None')}\n"
            )

        await update.message.reply_text("\n".join(lines))


# ── /testdaily ────────────────────────────────────────────────────────────────

@_coach_only
async def cmd_testdaily(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fire a daily check-in to all active clients immediately."""
    await update.message.reply_text("⏳ Sending daily check-ins to all active clients...")

    sent = 0
    failed = 0

    with get_session() as session:
        clients = get_all_active_clients(session)
        if not clients:
            await update.message.reply_text("No active clients found.")
            return

        for client in clients:
            try:
                recent_messages = get_recent_messages(session, client)
                question = generate_checkin_question(
                    client=client,
                    checkin_type="daily",
                    recent_messages=recent_messages,
                )

                await context.bot.send_message(
                    chat_id=client.telegram_group_id,
                    text=question,
                )

                save_message(
                    session=session,
                    client=client,
                    sender_role="bot",
                    message_text=question,
                )
                set_pending_checkin(session, client, "daily")
                sent += 1
                logger.info(f"[CMD] Daily check-in sent for '{client.name}'")

            except Exception as e:
                failed += 1
                logger.error(f"[CMD] Failed daily check-in for '{client.name}': {e}")

    status = f"✅ Daily check-ins sent: {sent}"
    if failed:
        status += f"\n❌ Failed: {failed} (check logs)"
    await update.message.reply_text(status)


# ── /testweekly ───────────────────────────────────────────────────────────────

@_coach_only
async def cmd_testweekly(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fire a weekly check-in to all active clients immediately."""
    await update.message.reply_text("⏳ Sending weekly check-ins to all active clients...")

    sent = 0
    failed = 0

    with get_session() as session:
        clients = get_all_active_clients(session)
        if not clients:
            await update.message.reply_text("No active clients found.")
            return

        for client in clients:
            try:
                recent_messages = get_recent_messages(session, client)
                recent_checkins = get_recent_checkins(session, client, limit=7)
                question = generate_checkin_question(
                    client=client,
                    checkin_type="weekly",
                    recent_messages=recent_messages,
                    recent_checkins=recent_checkins,
                )

                await context.bot.send_message(
                    chat_id=client.telegram_group_id,
                    text=question,
                )

                save_message(
                    session=session,
                    client=client,
                    sender_role="bot",
                    message_text=question,
                )
                set_pending_checkin(session, client, "weekly")
                sent += 1
                logger.info(f"[CMD] Weekly check-in sent for '{client.name}'")

            except Exception as e:
                failed += 1
                logger.error(f"[CMD] Failed weekly check-in for '{client.name}': {e}")

    status = f"✅ Weekly check-ins sent: {sent}"
    if failed:
        status += f"\n❌ Failed: {failed} (check logs)"
    await update.message.reply_text(status)


# ── /addclient ────────────────────────────────────────────────────────────────

@_coach_only
async def cmd_addclient(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Add a new client via command arguments.

    Usage:
      /addclient <group_id> <client_name> | <plan_summary>

    Example:
      /addclient -100123456789 Ananya Sharma | Weight loss: 1500 kcal, no sugar, 3L water daily

    The group_id is the negative number from Telegram (e.g. -1001234567890).
    Get it by sending a message in the group and checking getUpdates.
    """
    if not context.args or len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /addclient <group_id> <client_name> | <plan_summary>\n\n"
            "Example:\n"
            "/addclient -100123456789 Ananya | Weight loss: 1500 kcal, no sugar\n\n"
            "Get the group_id by typing /id inside your Telegram group!"
        )
        return

    # Parse: first arg is group_id, rest is "name | plan"
    group_id = context.args[0]
    rest = " ".join(context.args[1:])

    if "|" not in rest:
        await update.message.reply_text(
            "❌ Please separate the client name and plan with |\n"
            "Example: /addclient -100123456789 Ananya | 1500 kcal weight loss plan"
        )
        return

    name, plan = rest.split("|", 1)
    name = name.strip()
    plan = plan.strip()

    if not name or not plan:
        await update.message.reply_text("❌ Both client name and plan summary are required.")
        return

    with get_session() as session:
        # Check for duplicates
        existing = get_client_by_group(session, group_id)
        if existing:
            await update.message.reply_text(
                f"❌ A client already exists for group {group_id}: {existing.name}"
            )
            return

        client = add_client(
            session=session,
            name=name,
            telegram_group_id=group_id,
            plan_summary=plan,
        )

    await update.message.reply_text(
        f"✅ {name} added successfully!\n\n"
        f"• Group ID: {group_id}\n"
        f"• Plan: {plan[:100]}{'...' if len(plan) > 100 else ''}\n\n"
        "📝 Optional — set member IDs:\n"
        "Their customer and caretaker Telegram IDs can be set later by editing the DB or re-running seed.py."
    )
    logger.info(f"[CMD] New client added: '{name}' group={group_id}")


# ── /note (Custom Coaching Instructions) ──────────────────────────────────────

@_coach_only
async def cmd_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Add or update custom coaching instructions for a client.
    Usage:
      In a client group: /note Be extra strict about sugar!
      In DM: /note <group_id> Be extra strict about sugar!
      To clear instructions: /note clear (in group) or /note <group_id> clear
    """
    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "• In group chat: /note Be extra strict about sugar!\n"
            "• In DM: /note -100123456789 Be extra strict about sugar!\n"
            "• To clear: /note clear"
        )
        return

    chat_id = str(update.effective_chat.id)
    args = context.args

    with get_session() as session:
        # Check if first argument is a group ID (starts with - or digit)
        if args[0].startswith("-") or (args[0].isdigit() and len(args) > 1):
            group_id = args[0]
            instructions = " ".join(args[1:]).strip()
        else:
            group_id = chat_id
            instructions = " ".join(args).strip()

        client = get_client_by_group(session, group_id)
        if not client:
            await update.message.reply_text(
                f"❌ No client registered for group ID {group_id}.\n"
                f"If you are in DM, make sure to pass the Group ID: /note <group_id> <rules>"
            )
            return

        if not instructions or instructions.lower() == "clear":
            update_client_instructions(session, client, None)
            await update.message.reply_text(f"✅ Cleared custom coaching rules for {client.name}!")
            return

        update_client_instructions(session, client, instructions)
        await update.message.reply_text(
            f"✅ Custom coaching rules saved for {client.name}!\n\n"
            f"🎯 New Rules: {instructions}\n\n"
            f"💡 The AI will now strictly follow these rules whenever replying to {client.name}."
        )
        logger.info(f"[CMD] Updated custom instructions for '{client.name}': {instructions!r}")
