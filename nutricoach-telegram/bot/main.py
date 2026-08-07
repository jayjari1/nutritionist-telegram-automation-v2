"""
bot/main.py
-----------
Entry point for the NutriCoach Telegram Bot.
Run this file to start the entire bot system:
  python bot/main.py

This registers all handlers, starts the scheduler, and begins polling.
"""

import asyncio
import sys
import os

# Add project root to path so all imports work correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import setup_logging, get_logger
logger = get_logger("bot.main")

from sentry_init import init_sentry

from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    filters,
)

from config import validate_config, TELEGRAM_BOT_TOKEN, IS_PRODUCTION, WEBHOOK_URL, PORT
from bot.handlers.message_handler import handle_message
from bot.handlers.command_handler import (
    start,
    diet,
    progress,
    help_cmd,
    pause_client,
    resume_client,
    link_group,
    list_clients,
    join_group,
    set_client,
    set_caretaker,
    remove_caretaker,
    reset_roles,
    test_checkin,
)
from bot.scheduler import init_scheduler

# Only handle commands in groups, not in DMs
GROUP_FILTER = filters.ChatType.GROUPS


def main():
    """Starts the bot and all background services."""
    # Set up logging first
    setup_logging()
    logger.info("NutriCoach Bot starting...")

    # Initialize Sentry error tracking
    init_sentry()

    # Validate all required environment variables are set
    validate_config()

    # Build the Application
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # ── Register Command Handlers (GROUPS ONLY) ───────────────────────────────
    # Client commands
    app.add_handler(CommandHandler("start", start, GROUP_FILTER))
    app.add_handler(CommandHandler("diet", diet, GROUP_FILTER))
    app.add_handler(CommandHandler("progress", progress, GROUP_FILTER))
    app.add_handler(CommandHandler("help", help_cmd, GROUP_FILTER))

    # Nutritionist commands (silent - no response visible to others)
    app.add_handler(CommandHandler("pause", pause_client, GROUP_FILTER))
    app.add_handler(CommandHandler("resume", resume_client, GROUP_FILTER))
    app.add_handler(CommandHandler("link", link_group, GROUP_FILTER))
    app.add_handler(CommandHandler("list", list_clients, GROUP_FILTER))
    app.add_handler(CommandHandler("join", join_group, GROUP_FILTER))
    app.add_handler(CommandHandler("removecaretaker", remove_caretaker, GROUP_FILTER))

    # Setup commands (anyone can run)
    app.add_handler(CommandHandler("setclient", set_client, GROUP_FILTER))
    app.add_handler(CommandHandler("setcaretaker", set_caretaker, GROUP_FILTER))

    # Nutritionist reset command
    app.add_handler(CommandHandler("resetroles", reset_roles, GROUP_FILTER))

    # Nutritionist test command
    app.add_handler(CommandHandler("testcheckin", test_checkin, GROUP_FILTER))

    # ── Register Message Handler ──────────────────────────────────────────────
    # Only handles text messages in groups (not private chats)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
        handle_message,
    ))

    logger.info("All handlers registered.")

    # ── Start Scheduler ───────────────────────────────────────────────────────
    # Pass the bot instance to the scheduler so it can send messages
    scheduler = init_scheduler(app.bot)

    # ── Start Polling or Webhook ──────────────────────────────────────────────
    if IS_PRODUCTION and WEBHOOK_URL:
        logger.info(f"Production mode — starting webhook at {WEBHOOK_URL}")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=WEBHOOK_URL,
        )
    else:
        logger.info("Starting polling...")
        # drop_pending_updates=True ensures old bot instance's updates are ignored
        app.run_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )


if __name__ == "__main__":
    # Wrap main() in try/except for error recovery
    import time
    
    MAX_RETRIES = 5
    RETRY_DELAY = 10  # seconds
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            main()
            break  # If main() exits normally, break the loop
        except KeyboardInterrupt:
            logger.info("Bot stopped by user (Ctrl+C)")
            break
        except Exception as e:
            logger.error(f"Bot crashed on attempt {attempt}/{MAX_RETRIES}: {e}")
            if attempt < MAX_RETRIES:
                logger.info(f"Restarting in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.critical("Max retries reached. Bot shutting down permanently.")
                raise
