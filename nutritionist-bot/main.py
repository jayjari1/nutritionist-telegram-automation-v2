"""
main.py — Entry point for the Nutrition Bot.

Startup sequence:
  1. Validate environment variables
  2. Initialise SQLite database (create tables if missing)
  3. Build the Telegram Application (bot + handlers + commands)
  4. Start APScheduler (daily + weekly cron jobs)
  5. Run bot in long-polling mode (no public server needed for demo)
"""

import logging
import sys

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

import config  # validates env vars on import — will raise if missing
from db.database import init_db
from bot.handlers import handle_group_message
from bot.commands import (
    cmd_start,
    cmd_help,
    cmd_status,
    cmd_testdaily,
    cmd_testweekly,
    cmd_addclient,
    cmd_id,
    cmd_note,
)
from bot.scheduler import create_scheduler

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

# Quiet down noisy libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.INFO)

logger = logging.getLogger(__name__)


def main() -> None:
    """Run the bot."""

    print("\n" + "=" * 60)
    print("  🥗  Nutritionist Telegram Bot  —  V2 (Python)")
    print("=" * 60)
    print(f"  Coach     : {config.COACH_NAME}")
    print(f"  AI Model  : {config.GEMINI_MODEL}")
    print(f"  Timezone  : {config.TIMEZONE}")
    print(f"  Daily at  : {config.DAILY_CHECKIN_HOUR}:00")
    print(f"  Weekly on : {config.WEEKLY_CHECKIN_DAY.upper()} at {config.WEEKLY_CHECKIN_HOUR}:00")
    print(f"  DB path   : {config.DB_PATH}")
    print("=" * 60 + "\n")

    # ── Step 1: Initialise database ───────────────────────────────────────────
    init_db()

    # ── Step 2: Build Telegram application ────────────────────────────────────
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    # ── Step 3: Register command handlers ─────────────────────────────────────
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("testdaily", cmd_testdaily))
    app.add_handler(CommandHandler("testweekly", cmd_testweekly))
    app.add_handler(CommandHandler("addclient", cmd_addclient))
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CommandHandler("note", cmd_note))

    # ── Step 4: Register message handler ──────────────────────────────────────
    # Listen for text messages in groups and supergroups (not commands)
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
            handle_group_message,
        )
    )

    # ── Step 5: Start scheduler ───────────────────────────────────────────────
    scheduler = create_scheduler(app.bot)
    scheduler.start()

    # ── Step 6: Launch bot ────────────────────────────────────────────────────
    logger.info("✅ Bot is running! Press Ctrl+C to stop.\n")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
