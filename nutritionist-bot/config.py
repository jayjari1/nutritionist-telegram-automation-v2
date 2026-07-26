"""
config.py — Load and validate all environment variables.
All other modules import from here; nothing reads os.environ directly.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    """Get a required env var or raise a clear error."""
    val = os.getenv(key, "").strip()
    if not val:
        raise EnvironmentError(
            f"[CONFIG] Missing required environment variable: {key}\n"
            "  → Copy .env.example to .env and fill in all values."
        )
    return val


# ── Telegram ──────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = _require("TELEGRAM_BOT_TOKEN")

# Nutritionist's Telegram user ID (integer). Bot stays silent when she speaks
# and saves her messages as role='nutritionist'.
COACH_TELEGRAM_ID: int = int(_require("COACH_TELEGRAM_ID"))

COACH_NAME: str = os.getenv("COACH_NAME", "Coach").strip()

# ── Gemini ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = _require("GEMINI_API_KEY")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

# ── Scheduler ─────────────────────────────────────────────────────────────────
TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Kolkata").strip()
DAILY_CHECKIN_HOUR: int = int(os.getenv("DAILY_CHECKIN_HOUR", "19"))    # 7 PM
WEEKLY_CHECKIN_DAY: str = os.getenv("WEEKLY_CHECKIN_DAY", "sun").strip()  # Sunday
WEEKLY_CHECKIN_HOUR: int = int(os.getenv("WEEKLY_CHECKIN_HOUR", "18"))  # 6 PM

# ── Database ──────────────────────────────────────────────────────────────────
# SQLite for demo. For production (200+ clients) migrate to PostgreSQL.
DB_PATH: str = os.getenv("DB_PATH", "data/nutrition_bot.db").strip()

# ── AI behaviour ──────────────────────────────────────────────────────────────
# How many past messages to include in every Gemini call for context.
CONTEXT_MESSAGE_LIMIT: int = int(os.getenv("CONTEXT_MESSAGE_LIMIT", "30"))
