"""
ai/router.py
------------
The brain of the system.
Takes a client message, loads all context, calls AI, and returns a decision.
This is the single function called for EVERY client message.
"""

from logger import get_logger
logger = get_logger("ai.router")

import db.clients as db_clients
import db.nutritionists as db_nutritionists
import db.messages as db_messages
import db.checkins as db_checkins
import db.ai_rules as db_ai_rules
import db.queries as db_queries
import ai.gemini as gemini


def route(client_id: str, message_text: str, telegram_msg_id: int = None, sender_role: str = "client") -> dict:
    """
    Full pipeline for processing a client/caretaker message:
    1. Load client + nutritionist + rules + history
    2. Send to Gemini AI for decision
    3. Save message to DB
    4. Return result (action, reply, etc.)

    Returns:
    {
        "action": "handle" or "escalate",
        "reply": "message to send back in Telegram",
        "adherence": "on_track" / "partial" / "off_track" / None,
        "energy_level": int or None,
        "query_id": UUID string (only if escalating)
    }
    """

    # ── Step 1: Load all context ──────────────────────────────────────────────

    client = db_clients.get_by_id(client_id)
    if not client:
        logger.warning(f"Client not found: {client_id}")
        return {"action": "handle", "reply": "Hi! I'm having trouble finding your profile. Please contact support.", "adherence": None, "energy_level": None}

    nutritionist = db_nutritionists.get_by_id(client["nutritionist_id"])
    if not nutritionist:
        logger.warning(f"Nutritionist not found for client: {client_id}")
        return {"action": "handle", "reply": "Hi! I'm having a configuration issue. Please contact your doctor.", "adherence": None, "energy_level": None}

    logger.info(f"Processing message from {sender_role} for client {client['full_name']}")

    # ── Step 2: Load AI rules ─────────────────────────────────────────────────

    all_rules = db_ai_rules.get_all_for_client(nutritionist["id"], client_id)
    rules_text = db_ai_rules.format_rules_for_prompt(all_rules)

    # ── Step 3: Load recent conversation history ──────────────────────────────

    recent_messages = db_messages.get_recent(client_id, limit=10)
    history_text = db_messages.format_for_ai_context(recent_messages)

    # ── Step 4: Save client message to DB BEFORE processing ──────────────────

    db_messages.save(
        client_id=client_id,
        sender_role=sender_role,
        content=message_text,
        sender_name=client["full_name"] if sender_role == "client" else "Caretaker",
        telegram_msg_id=telegram_msg_id,
    )

    # ── Step 5: Call Gemini AI ────────────────────────────────────────────────

    result = gemini.evaluate(
        client=client,
        nutritionist=nutritionist,
        rules_text=rules_text,
        history_text=history_text,
        new_message=message_text,
    )

    logger.info(f"AI result: action={result['action']}, adherence={result['adherence']}")

    # ── Step 6: Handle result ─────────────────────────────────────────────────

    query_id = None

    if result["action"] == "handle":
        # Save AI reply to DB
        db_messages.save(
            client_id=client_id,
            sender_role="ai",
            content=result["reply"],
            sender_name="NutriCoach AI",
        )
        # Update today's checkin record
        db_checkins.update_today(
            client_id=client_id,
            client_message=message_text,
            ai_reply=result["reply"],
            adherence_status=result["adherence"],
            energy_level=result["energy_level"],
        )

    elif result["action"] == "escalate":
        # Save AI interim reply to DB
        db_messages.save(
            client_id=client_id,
            sender_role="ai",
            content=result["reply"],
            sender_name="NutriCoach AI",
        )
        # Create pending query record
        query = db_queries.create(
            client_id=client_id,
            nutritionist_id=nutritionist["id"],
            client_message=message_text,
            ai_assessment=result.get("escalation_reason", ""),
            ai_interim_reply=result["reply"],
        )
        query_id = query["id"]
        logger.info(f"Query escalated: {query_id}")

        # Update checkin to show no_response (AI couldn't classify due to escalation)
        db_checkins.update_today(
            client_id=client_id,
            client_message=message_text,
        )

    return {
        "action": result["action"],
        "reply": result["reply"],
        "adherence": result["adherence"],
        "energy_level": result["energy_level"],
        "query_id": query_id,
        "nutritionist_telegram_id": nutritionist.get("telegram_user_id"),
        "client_name": client["full_name"],
        "nutritionist_name": nutritionist["full_name"],
    }
