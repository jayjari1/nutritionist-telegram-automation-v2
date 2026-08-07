"""
sentry_init.py
--------------
Initialize Sentry for error monitoring.
Call this at the start of each process (bot and API).
Set SENTRY_DSN in .env to enable. If not set, Sentry is disabled.
"""

import os
from logger import get_logger

logger = get_logger("sentry")


def init_sentry():
    """
    Initialize Sentry error tracking.
    Only activates if SENTRY_DSN is set in environment.
    """
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        logger.info("Sentry not configured (SENTRY_DSN not set). Error tracking disabled.")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration

        # Configure Sentry with logging integration
        sentry_logging = LoggingIntegration(
            level=logging.INFO,        # Send info and above as breadcrumbs
            event_level=logging.ERROR  # Send errors as events
        )

        sentry_sdk.init(
            dsn=dsn,
            integrations=[sentry_logging],
            traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
            send_default_pii=True,   # Include user info in errors
            environment=os.getenv("APP_ENV", "development"),
        )

        logger.info("Sentry error tracking initialized.")

    except ImportError:
        logger.warning("sentry-sdk not installed. Run: pip install sentry-sdk")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
