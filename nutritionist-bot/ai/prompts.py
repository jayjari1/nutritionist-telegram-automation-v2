"""
ai/prompts.py — System prompt templates and the Gemini JSON extraction schema.

All text that goes into the AI lives here so it's easy to tune without
touching business logic.
"""

from db.models import Client, Message


# ── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """You are {coach_name}'s AI nutrition accountability assistant. You live inside a private Telegram group with exactly three members: the client, their caretaker (usually a parent or family member who prepares their food), and you.

This client's name is {client_name}.
Their nutrition plan: {plan_summary}
{custom_instructions_block}
Your responsibilities:
- Send brief, warm, specific check-in questions based on their ACTUAL plan — never generic questions like "how was your day".
- When the client or caretaker replies, respond like a supportive coach who knows their plan in detail. Keep replies to 1–3 sentences unless more is clearly needed.
- If the nutritionist ({coach_name}) has personally written something in the group, acknowledge their guidance naturally and align your tone with what they said.
- The whole point of this group is alignment between the client AND the caretaker. If one mentions something the other hasn't, gently surface it so both are aware.
- Keep continuity — refer back to earlier check-ins when relevant, like a coach who actually remembers previous conversations.
- You support both Hindi/Hinglish and English. Reply in the same language the user writes in. If they mix languages, you can too.
- You are NOT a doctor. If anything sounds medical or concerning, warmly advise them to contact {coach_name} directly or see a doctor. Never diagnose or give medical advice.
- When {coach_name} speaks in the group, do NOT reply to them. Their message is for the client and caretaker directly.

Keep your tone warm, encouraging, and human — never robotic or formal."""


def build_system_prompt(client: Client, coach_name: str) -> str:
    """Fill in the system prompt template for a specific client."""
    custom_block = ""
    if getattr(client, "custom_instructions", None):
        custom_block = (
            f"\n*** SPECIAL COACHING INSTRUCTIONS FOR {client.name.upper()} ***\n"
            f"{client.custom_instructions}\n"
            "You MUST strictly follow these special rules when replying or coaching this client!\n"
            "************************************************************************\n"
        )

    return SYSTEM_PROMPT_TEMPLATE.format(
        coach_name=coach_name,
        client_name=client.name,
        plan_summary=client.plan_summary,
        custom_instructions_block=custom_block,
    )


# ── Conversation Context Builder ──────────────────────────────────────────────

def build_conversation_context(messages: list[Message]) -> list[dict]:
    """
    Convert DB message rows into the Gemini `contents` format.
    Maps sender roles to model/user turns:
      - 'bot'          → model
      - everything else → user (with name prefix so AI knows who spoke)
    """
    contents = []

    role_labels = {
        "customer": "Client",
        "caretaker": "Caretaker",
        "nutritionist": "Nutritionist (Coach)",
        "bot": None,  # handled as model turn
    }

    for msg in messages:
        if msg.sender_role == "bot":
            contents.append({
                "role": "model",
                "parts": [{"text": msg.message_text}],
            })
        else:
            label = role_labels.get(msg.sender_role, msg.sender_role.title())
            contents.append({
                "role": "user",
                "parts": [{"text": f"[{label}]: {msg.message_text}"}],
            })

    return contents


# ── JSON Extraction Schema ────────────────────────────────────────────────────

EXTRACTION_SYSTEM_PROMPT = """You are a data extraction assistant for a nutrition coaching system.

Given a conversation between a client, their caretaker, and an AI coach, extract the following structured information from the client's/caretaker's latest reply.

Return ONLY valid JSON with exactly these fields. Do not add any explanation or extra text."""

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "adherence": {
            "type": "string",
            "enum": ["on_track", "partial", "off_track", "unclear"],
            "description": "How well the client followed their nutrition plan"
        },
        "energy_level": {
            "type": "string",
            "enum": ["low", "medium", "high", "not_mentioned"],
            "description": "Client's energy level as mentioned"
        },
        "mood": {
            "type": "string",
            "description": "Short description of client's mood, or null"
        },
        "symptoms": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Array of any symptoms mentioned. Empty array if none."
        },
        "caretaker_note": {
            "type": "string",
            "description": "Anything notable the caretaker specifically added, or null"
        },
        "needs_attention": {
            "type": "boolean",
            "description": "True if: missed meals 2+ days, any symptom mentioned, signs of distress, or anything requiring the human coach's attention"
        },
        "flag_reason": {
            "type": "string",
            "description": "Short reason why needs_attention is true, or null"
        },
        "summary": {
            "type": "string",
            "description": "One-line plain-English summary for the coach's records"
        }
    },
    "required": ["adherence", "energy_level", "mood", "symptoms", "caretaker_note", "needs_attention", "flag_reason", "summary"]
}


# ── Daily / Weekly Question Prompts ───────────────────────────────────────────

DAILY_QUESTION_PROMPT = """Based on this client's nutrition plan and recent check-in history, write ONE short, warm, specific daily check-in question.

Rules:
- Reference a SPECIFIC meal, food, or habit from their plan (never ask "how was your day")
- Maximum 2 sentences
- Friendly and encouraging tone
- If recent check-ins show a pattern (e.g. skipping lunch repeatedly), address that
- Support Hindi/Hinglish if the client typically writes in Hindi — but default to English

Return ONLY the question text. No greeting, no sign-off."""

WEEKLY_QUESTION_PROMPT = """Based on this client's nutrition plan and the past week of daily check-ins, write ONE thoughtful weekly check-in question.

Rules:
- Reference the overall week's trend (e.g. energy levels, adherence patterns, specific challenges)
- Ask about the biggest win AND the biggest challenge this week
- Maximum 3 sentences
- Warm and motivating tone
- Support Hindi/Hinglish if the client typically writes in Hindi

Return ONLY the question text. No greeting, no sign-off."""
