"""
seed.py — Seed 2 demo clients into the database.

Run this ONCE after setting up your real Telegram groups.
Fill in the placeholder values below with your actual Telegram IDs.

How to get IDs:
  1. Create a Telegram group, add the bot, client, and caretaker.
  2. Send any message in the group.
  3. Visit: https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
  4. Find the "chat" object → the "id" (negative number) is your group ID.
  5. Find each sender's "from" → "id" for their user IDs.
"""

from db.database import init_db, get_session
from db.queries import get_client_by_group, add_client

# ─────────────────────────────────────────────────────────────────────────────
# FILL IN YOUR REAL VALUES BELOW BEFORE RUNNING
# ─────────────────────────────────────────────────────────────────────────────

DEMO_CLIENTS = [
    {
        # ── Client 1: Weight Loss ─────────────────────────────────────────────
        "name": "Demo Client 1",

        # Replace with your actual Telegram group chat ID (negative number)
        # e.g. "-1001234567890"
        "telegram_group_id": "REPLACE_WITH_GROUP_1_ID",

        # Replace with the actual Telegram user IDs
        "customer_telegram_id": "REPLACE_WITH_CLIENT_1_TELEGRAM_ID",
        "caretaker_telegram_id": "REPLACE_WITH_CARETAKER_1_TELEGRAM_ID",

        "plan_summary": (
            "Weight loss plan for a 28-year-old female. "
            "Target: 1400 kcal/day. "
            "Meals: Breakfast at 8am (oats + fruit), Lunch at 1pm (dal + roti + sabzi + salad), "
            "Snack at 4pm (nuts or buttermilk), Dinner at 7:30pm (light — soup + paneer or egg). "
            "Avoid: fried food, sugar, maida, packaged snacks. "
            "Drink: 3 litres water daily, no cold drinks. "
            "Exercise: 30 min walk every morning. "
            "Focus areas: portion control, late-night snacking, and emotional eating triggers."
        ),
    },
    {
        # ── Client 2: Muscle Gain ─────────────────────────────────────────────
        "name": "Demo Client 2",

        # Replace with your actual Telegram group chat ID (negative number)
        # e.g. "-1009876543210"
        "telegram_group_id": "REPLACE_WITH_GROUP_2_ID",

        # Replace with the actual Telegram user IDs
        "customer_telegram_id": "REPLACE_WITH_CLIENT_2_TELEGRAM_ID",
        "caretaker_telegram_id": "REPLACE_WITH_CARETAKER_2_TELEGRAM_ID",

        "plan_summary": (
            "Muscle gain plan for a 22-year-old male. "
            "Target: 2800 kcal/day, 160g protein/day. "
            "Meals: Pre-workout at 7am (banana + peanut butter), "
            "Breakfast at 9am (4 eggs + 2 roti + milk), "
            "Lunch at 1pm (chicken/paneer 200g + rice + dal + salad), "
            "Post-workout snack at 5pm (protein shake or curd + fruit), "
            "Dinner at 8pm (fish or chicken + veggies + roti). "
            "Avoid: skipping meals, excess junk food. "
            "Drink: 4 litres water daily. "
            "Gym: 5 days/week strength training. "
            "Focus areas: hitting daily protein targets, meal timing around workouts, sleep quality."
        ),
    },
]

# ─────────────────────────────────────────────────────────────────────────────


def seed() -> None:
    """Insert demo clients if they don't already exist."""
    init_db()

    with get_session() as session:
        for data in DEMO_CLIENTS:
            # Skip if already seeded
            existing = get_client_by_group(session, data["telegram_group_id"])
            if existing:
                print(f"[SEED] Skipping '{data['name']}' — already exists.")
                continue

            client = add_client(
                session=session,
                name=data["name"],
                telegram_group_id=data["telegram_group_id"],
                plan_summary=data["plan_summary"],
                customer_telegram_id=data.get("customer_telegram_id"),
                caretaker_telegram_id=data.get("caretaker_telegram_id"),
            )
            print(f"[SEED] ✅ Added client: '{client.name}' (ID: {client.id})")

    print("\n[SEED] Done! Your demo clients are ready.")
    print(
        "\n📝 NEXT STEPS:\n"
        "  1. Create your Telegram groups (one per client)\n"
        "  2. Add your bot to each group\n"
        "  3. Get the group IDs from getUpdates\n"
        "  4. Update the DEMO_CLIENTS list in seed.py with real IDs\n"
        "  5. Re-run: python seed.py\n"
        "  6. Start the bot: python main.py\n"
    )


if __name__ == "__main__":
    seed()
