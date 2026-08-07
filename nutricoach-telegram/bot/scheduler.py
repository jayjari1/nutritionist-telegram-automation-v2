"""
bot/scheduler.py
----------------
Handles all time-based automation:
1. Daily check-in messages sent to each client's Telegram group at their scheduled time
2. Weekly summary sent every Sunday
3. Expiry warnings sent when program ending within 3 or 7 days
4. Auto-expire programs that have passed their end date
"""

import asyncio
from datetime import datetime, date, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from logger import get_logger
logger = get_logger("bot.scheduler")

import db.clients as db_clients
import db.checkins as db_checkins
import db.nutritionists as db_nutritionists
import ai.gemini as gemini

# Bot instance is injected from main.py
_bot = None


def init_scheduler(bot) -> AsyncIOScheduler:
    """
    Initialize and start the scheduler.
    Called once from main.py after bot is set up.
    Returns the scheduler instance.
    """
    global _bot
    _bot = bot

    scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")  # IST timezone

    # Run every minute — checks which clients need a check-in RIGHT NOW
    scheduler.add_job(
        _send_due_checkins,
        trigger="interval",
        minutes=1,
        id="daily_checkins",
        name="Daily Check-in Sender",
    )

    # Run every Sunday at 8:00 PM IST — weekly summaries
    scheduler.add_job(
        _send_weekly_summaries,
        trigger="cron",
        day_of_week="sun",
        hour=20,
        minute=0,
        id="weekly_summaries",
        name="Weekly Progress Summaries",
    )

    # Run every day at 9:00 AM IST — check for expiring programs
    scheduler.add_job(
        _check_expirations,
        trigger="cron",
        hour=9,
        minute=0,
        id="expiry_check",
        name="Expiry & Expiring Soon Checker",
    )

    scheduler.start()
    logger.info("Scheduler started — daily check-ins, weekly summaries, expiry checks active.")
    return scheduler


# ── Job 1: Daily Check-ins ────────────────────────────────────────────────────

async def _send_due_checkins():
    """
    Runs every minute. Finds all active clients whose check-in time matches now.
    Sends the daily check-in message to their Telegram group.
    """
    if not _bot:
        return

    from zoneinfo import ZoneInfo
    current_time = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%H:%M")
    try:
        due_clients = db_clients.get_due_for_checkin(current_time)
    except Exception as e:
        logger.error(f"Failed to fetch due check-ins: {e}")
        return

    for client in due_clients:
        try:
            # Skip if nutritionist is paused/expired
            nutritionist = db_nutritionists.get_by_id(client["nutritionist_id"])
            if not nutritionist or nutritionist.get("status") != "active":
                continue

            # Skip if already sent today
            if db_checkins.sent_today(client["id"]):
                continue

            group_id = client.get("telegram_group_id")
            if not group_id:
                logger.warning(f"Client {client['full_name']} has no group ID — skipping check-in")
                continue

            message = _build_checkin_message(client)
            await _bot.send_message(chat_id=group_id, text=message, parse_mode="Markdown")

            # Create blank check-in record for today
            db_checkins.create_today(client["id"])

            logger.info(f"Check-in sent to {client['full_name']} at {current_time}")

        except Exception as e:
            logger.error(f"Failed to send check-in to {client.get('full_name', 'Unknown')}: {e}")


def _build_checkin_message(client: dict) -> str:
    """Builds a personalised daily check-in message."""
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
        emoji = "🌅"
    elif hour < 17:
        greeting = "Good afternoon"
        emoji = "☀️"
    else:
        greeting = "Good evening"
        emoji = "🌙"

    first_name = client["full_name"].split()[0]
    return (
        f"{emoji} *{greeting}, {first_name}!*\n\n"
        f"How was your diet today? Tell me in your own words — "
        f"what did you eat and how are you feeling? 😊\n\n"
        f"_(Hindi, English, or Hinglish — whatever feels natural!)_"
    )


# ── Job 2: Weekly Summary ─────────────────────────────────────────────────────

async def _send_weekly_summaries():
    """
    Runs every Sunday at 8pm IST.
    Generates and sends a weekly progress summary to every active client's group.
    """
    if not _bot:
        return

    # Get all active clients
    from db.client import supabase
    try:
        res = supabase.table("clients").select("*").eq("status", "active").execute()
        all_clients = res.data or []
    except Exception as e:
        logger.error(f"Failed to fetch active clients for weekly summaries: {e}")
        return

    for client in all_clients:
        try:
            group_id = client.get("telegram_group_id")
            if not group_id:
                continue

            nutritionist = db_nutritionists.get_by_id(client["nutritionist_id"])
            if not nutritionist or nutritionist.get("status") != "active":
                continue

            stats = db_checkins.get_weekly_stats(client["id"])
            checkins = db_checkins.get_recent(client["id"], limit=7)

            summary = gemini.generate_weekly_summary(client, nutritionist, stats, checkins)
            await _bot.send_message(chat_id=group_id, text=summary)

            logger.info(f"Weekly summary sent to {client['full_name']}")

        except Exception as e:
            logger.error(f"Failed to send weekly summary to {client.get('full_name', 'Unknown')}: {e}")


# ── Job 3: Expiry Checking ────────────────────────────────────────────────────

async def _check_expirations():
    """
    Runs every day at 9am IST.
    1. Sends expiry warnings (3 days and 7 days before program ends)
    2. Auto-expires programs that have already passed their end date
    """
    if not _bot:
        return

    today = date.today()

    # Find clients expiring in exactly 7 days
    try:
        expiring_7 = db_clients.get_expiring_soon(days_threshold=7)
        # Find clients expiring in exactly 3 days
        expiring_3 = db_clients.get_expiring_soon(days_threshold=3)
    except Exception as e:
        logger.error(f"Failed to fetch expiring clients: {e}")
        expiring_7 = []
        expiring_3 = []

    # Send 7-day warning
    for client in expiring_7:
        if db_clients.days_remaining(client) == 7:
            await _send_expiry_warning(client, days_left=7)

    # Send 3-day warning
    for client in expiring_3:
        if db_clients.days_remaining(client) == 3:
            await _send_expiry_warning(client, days_left=3)

    # Auto-expire programs past their end date
    from db.client import supabase
    try:
        res = (
            supabase.table("clients")
            .select("*")
            .eq("status", "active")
            .lt("program_end", today.isoformat())
            .execute()
        )
        expired_clients = res.data or []
    except Exception as e:
        logger.error(f"Failed to fetch expired clients: {e}")
        expired_clients = []

    for client in expired_clients:
        db_clients.set_status(client["id"], "expired")
        group_id = client.get("telegram_group_id")
        if group_id:
            try:
                await _bot.send_message(
                    chat_id=group_id,
                    text=(
                        f"📅 {client['full_name']}'s {client.get('program_type', '')} program has concluded today.\n\n"
                        f"Thank you for your dedication throughout this journey! 🌿\n"
                        f"Your full history is saved. Contact your nutritionist to continue or start a new program."
                    )
                )
            except Exception as e:
                logger.error(f"Could not send expiry message: {e}")
        logger.info(f"Auto-expired: {client['full_name']}")


async def _send_expiry_warning(client: dict, days_left: int):
    """Sends a warning message to the group when program is ending soon."""
    group_id = client.get("telegram_group_id")
    if not group_id:
        return

    try:
        await _bot.send_message(
            chat_id=group_id,
            text=(
                f"⚠️ *Program Ending Soon — {days_left} Days Left*\n\n"
                f"{client['full_name']}'s {client.get('program_type', 'Nutrition')} program "
                f"ends in *{days_left} days*.\n\n"
                f"Please contact your nutritionist to discuss renewal or next steps! 💬"
            ),
            parse_mode="Markdown"
        )
        logger.info(f"Expiry warning ({days_left} days) sent to {client['full_name']}")
    except Exception as e:
        logger.error(f"Could not send expiry warning: {e}")
