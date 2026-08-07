"""
api/webhook.py
--------------
FastAPI server that the Next.js web app calls.
Run with: uvicorn api.webhook:app --reload --port 8000
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from logger import setup_logging, get_logger
from sentry_init import init_sentry
from config import PORT
from api.routes import auth, clients, checkins, queries, rules, admin, messages, config

# Initialize logging and Sentry
setup_logging()
logger = get_logger("api.webhook")
init_sentry()

app = FastAPI(
    title="NutriCoach API",
    description="Backend API for the NutriCoach web app",
    version="1.0.0",
)

# CORS — allow Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(clients.router, prefix="/clients", tags=["Clients"])
app.include_router(checkins.router, prefix="/clients", tags=["Check-ins"])
app.include_router(queries.router, prefix="/queries", tags=["Pending Queries"])
app.include_router(rules.router, prefix="/rules", tags=["AI Rules"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(messages.router, prefix="/clients", tags=["Messages"])
app.include_router(config.router, prefix="/config", tags=["Config"])


@app.get("/")
def root():
    return {"message": "NutriCoach API is running", "version": "1.0.0"}


@app.get("/health")
def health():
    """Detailed health check — verifies database connectivity."""
    from datetime import datetime
    checks = {
        "api": "ok",
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Check database connectivity
    try:
        from db.client import supabase
        supabase.table("nutritionists").select("id").limit(1).execute()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)[:100]}"
        logger.error(f"Health check — database error: {e}")

    # Check if all critical env vars are set
    from config import TELEGRAM_BOT_TOKEN, SUPABASE_URL, GEMINI_API_KEY
    checks["config"] = "ok" if all([TELEGRAM_BOT_TOKEN, SUPABASE_URL, GEMINI_API_KEY]) else "incomplete"

    overall_status = "ok" if checks.get("database") == "ok" else "degraded"

    return {
        "status": overall_status,
        **checks
    }
