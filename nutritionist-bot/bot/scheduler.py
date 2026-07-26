"""
bot/scheduler.py — APScheduler cron jobs for daily and weekly check-ins.

Jobs:
  - daily_checkin_job   : Fires every day at DAILY_CHECKIN_HOUR (e.g. 19:00 IST)
  - weekly_checkin_job  : Fires every WEEKLY_CHECKIN_DAY at WEEKLY_CHECKIN_HOUR

Both jobs iterate all active clients and send personalised check-in questions.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import config
from db.database import get_session
from db.queries import (
    get_all_active_clients,
    get_recent_messages,
    get_recent_checkins,
    save_message,
    set_pending_checkin,
)
from ai.gemini import generate_checkin_question

logger = logging.getLogger(__name__)


async def _send_checkin_to_all(bot, checkin_type: str) -> None:
    """
    Core logic shared by both daily and weekly jobs.
    Generates a personalised question for each active client and sends it.
    """
    logger.info(f"[SCHEDULER] Running {checkin_type} check-in job...")
    sent = 0
    failed = 0

    with get_session() as session:
        clients = get_all_active_clients(session)

        if not clients:
            logger.info("[SCHEDULER] No active clients — skipping.")
            return

        for client in clients:
            try:
                recent_messages = get_recent_messages(session, client)
                recent_checkins = (
                    get_recent_checkins(session, client, limit=7)
                    if checkin_type == "weekly"
                    else None
                )

                question = generate_checkin_question(
                    client=client,
                    checkin_type=checkin_type,
                    recent_messages=recent_messages,
                    recent_checkins=recent_checkins,
                )

                # Send to the Telegram group
                await bot.send_message(
                    chat_id=client.telegram_group_id,
                    text=question,
                )

                # Save bot's question to message log
                save_message(
                    session=session,
                    client=client,
                    sender_role="bot",
                    message_text=question,
                )

                # Mark that a check-in is pending for this client
                set_pending_checkin(session, client, checkin_type)

                sent += 1
                logger.info(
                    f"[SCHEDULER] {checkin_type.capitalize()} check-in sent to '{client.name}'"
                )

            except Exception as e:
                failed += 1
                logger.error(
                    f"[SCHEDULER] Failed {checkin_type} check-in for '{client.name}': {e}"
                )

    logger.info(
        f"[SCHEDULER] {checkin_type.capitalize()} job done — "
        f"sent={sent}, failed={failed}"
    )


def create_scheduler(bot) -> AsyncIOScheduler:
    """
    Create and return the APScheduler instance with both jobs registered.
    Call scheduler.start() after the bot is running.

    Args:
        bot: The Telegram Bot instance (from python-telegram-bot application).
    """
    scheduler = AsyncIOScheduler(timezone=config.TIMEZONE)

    # ── Daily check-in ────────────────────────────────────────────────────────
    scheduler.add_job(
        func=_send_checkin_to_all,
        trigger=CronTrigger(
            hour=config.DAILY_CHECKIN_HOUR,
            minute=0,
            timezone=config.TIMEZONE,
        ),
        args=[bot, "daily"],
        id="daily_checkin",
        name="Daily nutrition check-in",
        replace_existing=True,
    )

    # ── Weekly check-in ───────────────────────────────────────────────────────
    # WEEKLY_CHECKIN_DAY is a string like 'sun', 'mon', etc.
    scheduler.add_job(
        func=_send_checkin_to_all,
        trigger=CronTrigger(
            day_of_week=config.WEEKLY_CHECKIN_DAY,
            hour=config.WEEKLY_CHECKIN_HOUR,
            minute=0,
            timezone=config.TIMEZONE,
        ),
        args=[bot, "weekly"],
        id="weekly_checkin",
        name="Weekly nutrition check-in",
        replace_existing=True,
    )

    logger.info(
        f"[SCHEDULER] Jobs registered:\n"
        f"  • Daily  — every day at {config.DAILY_CHECKIN_HOUR}:00 {config.TIMEZONE}\n"
        f"  • Weekly — every {config.WEEKLY_CHECKIN_DAY} at {config.WEEKLY_CHECKIN_HOUR}:00 {config.TIMEZONE}"
    )

    return scheduler
