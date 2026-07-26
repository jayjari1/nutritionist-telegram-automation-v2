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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import PORT
from api.routes import auth, clients, checkins, queries, rules, admin, messages, config

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
    return {"status": "ok"}
