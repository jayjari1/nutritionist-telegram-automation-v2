"""
Run this once to insert test data into Supabase.
Usage: python setup_test_data.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()
from db.client import supabase

print("Setting up test data...\n")

# 1. Create a test nutritionist
nutritionist_data = {
    "full_name": "Dr. Test Nutritionist",
    "clinic_name": "Test Clinic",
    "email": "test@nutricoach.in",
    "password": "hashed_password_here",
    "telegram_user_id": 0,  # UPDATE: put your own Telegram user ID here
    "status": "active",
}

# Check if nutritionist already exists
existing = supabase.table("nutritionists").select("*").eq("email", "test@nutricoach.in").execute()
if existing.data:
    nutritionist = existing.data[0]
    print(f"Nutritionist already exists: {nutritionist['id']}")
else:
    res = supabase.table("nutritionists").insert(nutritionist_data).execute()
    nutritionist = res.data[0]
    print(f"Created nutritionist: {nutritionist['id']}")

# 2. Create a test client
client_data = {
    "nutritionist_id": nutritionist["id"],
    "full_name": "Test Patient",
    "telegram_user_id": 0,  # UPDATE: put client's Telegram user ID here
    "telegram_group_id": 6159056602,  # Your test group ID
    "program_type": "Weight Management",
    "program_duration": 60,
    "program_start": "2026-07-21",
    "checkin_time": "19:00:00",
    "diet_chart": "Morning: Oats with milk\nLunch: Rice + Dal + Vegetables\nDinner: Roti + Sabzi\nSnacks: Fruits",
    "status": "active",
}

# Check if client already exists for this group
existing_client = supabase.table("clients").select("*").eq("telegram_group_id", 6159056602).execute()
if existing_client.data:
    client = existing_client.data[0]
    print(f"Client already exists: {client['id']}")
else:
    res = supabase.table("clients").insert(client_data).execute()
    client = res.data[0]
    print(f"Created client: {client['id']}")

print("\n--- TEST DATA READY ---")
print(f"Nutritionist ID: {nutritionist['id']}")
print(f"Client ID: {client['id']}")
print(f"Group ID: 6159056602")
print("\nNow restart the bot and send /start in the Telegram group!")
