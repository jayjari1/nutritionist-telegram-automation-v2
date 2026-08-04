"""
bot/handlers/command_handler.py
--------------------------------
Handles Telegram commands for setup and management.
"""

from telegram import Update
from telegram.ext import ContextTypes

import db.clients as db_clients
import db.nutritionists as db_nutritionists
import db.checkins as db_checkins


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start — Welcome message + diet chart."""
    group_id = update.message.chat.id
    try:
        client = db_clients.get_by_group_id(group_id)
    except Exception as e:
        print(f"[DEBUG] start() DB error: {type(e).__name__}: {e}")
        return

    if not client:
        await update.message.reply_text(
            "Welcome! This group is managed by NutriCoach AI.\n"
            "Please wait for your nutritionist to set up your program."
        )
        return

    nutritionist = db_nutritionists.get_by_id(client["nutritionist_id"])
    nut_name = nutritionist["full_name"] if nutritionist else "your nutritionist"

    welcome = (
        f"Welcome, {client['full_name']}!\n\n"
        f"{nut_name} has set up your {client.get('program_duration', 60)}-day "
        f"*{client.get('program_type', 'Nutrition')}* program.\n\n"
        f"I'm *NutriCoach AI* — your daily check-in companion!\n"
        f"I'll message you every evening at {_format_time(client.get('checkin_time', '19:00:00'))}.\n\n"
        f"Your diet plan is below. Any questions? Just ask here!"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")

    if client.get("diet_chart"):
        await update.message.reply_text(
            f"*Your Diet Plan:*\n\n{client['diet_chart']}",
            parse_mode="Markdown"
        )


async def diet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/diet — Resend diet chart."""
    group_id = update.message.chat.id
    try:
        client = db_clients.get_by_group_id(group_id)
    except Exception:
        return

    if not client:
        return

    if client.get("diet_chart"):
        await update.message.reply_text(
            f"*{client['full_name']}'s Diet Plan:*\n\n{client['diet_chart']}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("No diet chart uploaded yet. Ask your nutritionist.")


async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/progress — Last 7 days summary."""
    group_id = update.message.chat.id
    try:
        client = db_clients.get_by_group_id(group_id)
    except Exception:
        return

    if not client:
        return

    stats = db_checkins.get_weekly_stats(client["id"])
    from db.clients import days_remaining
    days_left = days_remaining(client)

    summary = (
        f"*{client['full_name']}'s Weekly Progress*\n\n"
        f"On Track: {stats['on_track']} days\n"
        f"Partial: {stats['partial']} days\n"
        f"Off Track: {stats['off_track']} days\n"
        f"No Response: {stats['no_response']} days\n\n"
        f"Consistency: *{stats['consistency_pct']}%*\n"
        f"Days remaining: *{days_left}*"
    )
    await update.message.reply_text(summary, parse_mode="Markdown")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/help — Available commands."""
    help_text = (
        "*NutriCoach AI — Commands*\n\n"
        "/diet — View your diet plan\n"
        "/progress — View your weekly summary\n"
        "/help — Show this message\n\n"
        "*Setup (run once):*\n"
        "/setclient — Run this to become the patient\n"
        "/setcaretaker — Run this to become the caretaker\n\n"
        "*Note:* If wrongly assigned, run the other command to swap."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def pause_client(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/pause — Nutritionist pauses check-ins. Silent command."""
    group_id = update.message.chat.id
    try:
        client = db_clients.get_by_group_id(group_id)
    except Exception:
        return
    if not client:
        return

    sender_id = update.message.from_user.id
    nutritionist = db_nutritionists.get_by_id(client["nutritionist_id"])
    if not nutritionist or sender_id != nutritionist.get("telegram_user_id"):
        return  # Silent - don't respond

    db_clients.set_status(client["id"], "paused")
    # No response - silent command


async def resume_client(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/resume — Nutritionist resumes check-ins. Silent command."""
    group_id = update.message.chat.id
    try:
        client = db_clients.get_by_group_id(group_id)
    except Exception:
        return
    if not client:
        return

    sender_id = update.message.from_user.id
    nutritionist = db_nutritionists.get_by_id(client["nutritionist_id"])
    if not nutritionist or sender_id != nutritionist.get("telegram_user_id"):
        return  # Silent - don't respond

    db_clients.set_status(client["id"], "active")
    # No response - silent command


async def link_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/link <client_name> — Nutritionist links group. Silent command."""
    sender_id = update.message.from_user.id
    group_id = update.message.chat.id

    nutritionist = db_nutritionists.get_by_telegram_id(sender_id)
    if not nutritionist:
        return  # Silent

    if not context.args:
        return  # Silent

    client_name = " ".join(context.args)

    all_clients = db_clients.get_all_for_nutritionist(nutritionist["id"])
    matches = [c for c in all_clients if client_name.lower() in c["full_name"].lower()]

    if not matches:
        return  # Silent

    if len(matches) > 1:
        return  # Silent

    client = matches[0]
    db_clients.set_group_id(client["id"], group_id)
    # No response - silent command


async def list_clients(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/list — Nutritionist sees all clients. Silent command."""
    sender_id = update.message.from_user.id

    nutritionist = db_nutritionists.get_by_telegram_id(sender_id)
    if not nutritionist:
        return  # Silent

    all_clients = db_clients.get_all_for_nutritionist(nutritionist["id"])

    if not all_clients:
        return  # Silent

    # Build message but don't send to group - would be visible to client
    # This command should only work in DM with bot, but we blocked DMs
    # So this is effectively disabled for now
    # No response - silent command


# ══════════════════════════════════════════════════════════════════════════════
# SETUP COMMANDS - Simple! Anyone can run them.
# ══════════════════════════════════════════════════════════════════════════════

async def join_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /join <CODE> — Nutritionist links group to a client.
    """
    sender_id = update.message.from_user.id
    sender_name = update.message.from_user.full_name
    group_id = update.message.chat.id

    print(f"[DEBUG /join] sender_id={sender_id}, sender_name={sender_name}, group_id={group_id}")

    nutritionist = db_nutritionists.get_by_telegram_id(sender_id)
    print(f"[DEBUG /join] nutritionist found: {nutritionist}")

    if not nutritionist:
        await update.message.reply_text(
            f"Only nutritionists can use this command.\n\n"
            f"Your Telegram ID: {sender_id}\n"
            f"If you are a nutritionist, ask admin to link your Telegram ID."
        )
        return

    if not context.args:
        await update.message.reply_text("Usage: /join <CODE>\nGet the code from your dashboard when you add a client.")
        return

    code = context.args[0].strip().upper()

    from db.invite_codes import find_by_code
    client = find_by_code(code)

    if not client:
        await update.message.reply_text(f"Invalid code: {code}\nPlease check the code from your dashboard.")
        return

    if client.get("telegram_group_id") and client["telegram_group_id"] != group_id:
        await update.message.reply_text("This code is already linked to a different group.")
        return

    db_clients.update(client["id"], {"telegram_group_id": group_id})

    await update.message.reply_text(
        f"Setup complete!\n\n"
        f"Client: {client['full_name']}\n"
        f"Group linked successfully.\n\n"
        f"Next steps:\n"
        f"1. Client sends /setclient to identify themselves\n"
        f"2. Optional: Caretaker sends /setcaretaker\n"
        f"3. Bot will start daily check-ins at the scheduled time"
    )

    print(f"[LINKED] Nutritionist linked group to {client['full_name']}")


async def set_client(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /setclient — The person who sends THIS command becomes the patient!
    No arguments needed. Just type /setclient and you're set.
    If someone was wrongly assigned, they can run /setclient again to reassign.
    """
    sender_id = update.message.from_user.id
    sender_name = update.message.from_user.full_name
    group_id = update.message.chat.id

    print(f"[DEBUG /setclient] sender_id={sender_id}, sender_name={sender_name}, group_id={group_id}")

    try:
        client = db_clients.get_by_group_id(group_id)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)[:200]}")
        return

    if not client:
        await update.message.reply_text("No client linked to this group. Ask nutritionist to run /join first.")
        return

    # Check if already set as caretaker — clear it first so they can become client
    if sender_id == client.get("caretaker_telegram"):
        db_clients.update(client["id"], {
            "caretaker_telegram": None,
            "caretaker_name": None,
        })
        # Continue to set as client below

    # Check if already set as client
    if sender_id == client.get("telegram_user_id"):
        await update.message.reply_text("You are already set as the patient!")
        return

    # Set as client
    db_clients.update(client["id"], {"telegram_user_id": sender_id})

    await update.message.reply_text(
        f"You ({sender_name}) are now set as the PATIENT!\n\n"
        f"The AI will respond to your messages."
    )

    print(f"[CLIENT] {sender_name} ({sender_id}) set as client for {client['full_name']}")


async def set_caretaker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /setcaretaker — The person who sends THIS command becomes the caretaker!
    No arguments needed. Just type /setcaretaker and you're set.
    If someone was wrongly assigned, they can run /setcaretaker again to reassign.
    """
    sender_id = update.message.from_user.id
    sender_name = update.message.from_user.full_name
    group_id = update.message.chat.id

    try:
        client = db_clients.get_by_group_id(group_id)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)[:200]}")
        return

    if not client:
        await update.message.reply_text("No client linked to this group. Ask nutritionist to run /join first.")
        return

    # Check if already set as client — clear it first so they can become caretaker
    if sender_id == client.get("telegram_user_id"):
        db_clients.update(client["id"], {
            "telegram_user_id": None,
        })
        # Continue to set as caretaker below

    # Check if already set as caretaker
    if sender_id == client.get("caretaker_telegram"):
        await update.message.reply_text("You are already set as the caretaker!")
        return

    # Set as caretaker
    db_clients.update(client["id"], {
        "caretaker_telegram": sender_id,
        "caretaker_name": sender_name,
    })

    await update.message.reply_text(
        f"You ({sender_name}) are now set as the CARETAKER!\n\n"
        f"Your messages will be logged as care notes."
    )

    print(f"[CARETAKER] {sender_name} ({sender_id}) set as caretaker for {client['full_name']}")


async def remove_caretaker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/removecaretaker — Nutritionist removes caretaker. Silent command."""
    sender_id = update.message.from_user.id
    group_id = update.message.chat.id

    try:
        client = db_clients.get_by_group_id(group_id)
    except Exception:
        return

    if not client:
        return  # Silent

    nutritionist = db_nutritionists.get_by_id(client["nutritionist_id"])
    if not nutritionist or sender_id != nutritionist.get("telegram_user_id"):
        return  # Silent

    if not client.get("caretaker_telegram"):
        return  # Silent

    db_clients.update(client["id"], {
        "caretaker_telegram": None,
        "caretaker_name": None,
    })

    # No response - silent command
    print(f"[CARETAKER] Removed caretaker for {client['full_name']}")


async def reset_roles(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/resetroles — Nutritionist clears both client and caretaker. Silent command."""
    sender_id = update.message.from_user.id
    group_id = update.message.chat.id

    try:
        client = db_clients.get_by_group_id(group_id)
    except Exception:
        return

    if not client:
        return  # Silent

    nutritionist = db_nutritionists.get_by_id(client["nutritionist_id"])
    if not nutritionist or sender_id != nutritionist.get("telegram_user_id"):
        return  # Silent

    db_clients.update(client["id"], {
        "telegram_user_id": None,
        "caretaker_telegram": None,
        "caretaker_name": None,
    })

    # No response - silent command
    print(f"[RESET] Cleared client and caretaker for {client['full_name']}")


async def test_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/testcheckin — Nutritionist manually triggers a check-in message. Visible to all."""
    sender_id = update.message.from_user.id
    group_id = update.message.chat.id

    try:
        client = db_clients.get_by_group_id(group_id)
    except Exception:
        return

    if not client:
        await update.message.reply_text("No client linked to this group.")
        return

    nutritionist = db_nutritionists.get_by_id(client["nutritionist_id"])
    if not nutritionist or sender_id != nutritionist.get("telegram_user_id"):
        return  # Silent

    # Build the same check-in message the scheduler sends
    from datetime import datetime
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
        emoji = "🌅"
    elif hour < 17:
        greeting = "Good afternoon"
        emoji = "☀️"
    else:
        greeting = "Good evening"
        emoji = "🌙"

    first_name = client["full_name"].split()[0]
    message = (
        f"{emoji} *{greeting}, {first_name}!*\n\n"
        f"How was your diet today? Tell me in your own words — "
        f"what did you eat and how are you feeling? 😊\n\n"
        f"_(Hindi, English, or Hinglish — whatever feels natural!)_"
    )

    await update.message.reply_text(message, parse_mode="Markdown")
    print(f"[TEST] Manual check-in sent to {client['full_name']}")


# ══════════════════════════════════════════════════════════════════════════════
# Helper
# ══════════════════════════════════════════════════════════════════════════════

def _format_time(time_str: str) -> str:
    """Formats '19:00:00' to '7:00 PM'"""
    try:
        from datetime import datetime
        t = datetime.strptime(time_str[:5], "%H:%M")
        return t.strftime("%-I:%M %p")
    except Exception:
        return time_str
