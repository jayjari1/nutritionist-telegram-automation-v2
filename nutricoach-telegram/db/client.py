"""
db/client.py
------------
Supabase connection singleton.
All other db modules import `supabase` from here.
"""

import traceback
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
from logger import get_logger

logger = get_logger("db.client")

logger.info(f"Supabase URL: {SUPABASE_URL}")
logger.info(f"Supabase key prefix: {SUPABASE_SERVICE_KEY[:20]}...")

# Single shared instance used everywhere
# Using SERVICE_KEY so we bypass Row Level Security (admin-level access)
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    logger.info("Supabase client created successfully")
except Exception as e:
    logger.error(f"Failed to create Supabase client: {type(e).__name__}: {e}")
    traceback.print_exc()
    raise
