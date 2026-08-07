"""
ai/gemini.py
------------
Google Gemini AI integration.
Builds the full dynamic prompt and returns a structured response.
"""

import json
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL
from logger import get_logger

logger = get_logger("ai.gemini")

# Configure Gemini on import
genai.configure(api_key=GEMINI_API_KEY)
_model = genai.GenerativeModel(GEMINI_MODEL)


def build_system_prompt(client: dict, nutritionist: dict, rules_text: str, history_text: str) -> str:
    """
    Builds the full AI system prompt by injecting all dynamic context.
    This is sent to Gemini before every client message.
    """
    from db.clients import days_remaining
    days_left = days_remaining(client)

    return f"""You are NutriCoach AI, the clinical nutrition assistant for {nutritionist['full_name']} ({nutritionist.get('clinic_name', 'NutriCoach Clinic')}).

== CLIENT CONTEXT ==
Name: {client['full_name']}
Program: {client.get('program_type', 'Nutrition Program')} ({days_left} days remaining)
Program End Date: {client.get('program_end', 'Not set')}

== DIET PLAN ==
{client.get('diet_chart', 'Diet plan not uploaded yet.')}

== RULES & INSTRUCTIONS ==
{rules_text}

== RECENT CONVERSATION HISTORY ==
{history_text if history_text else 'No previous messages.'}

== IMPORTANT: DOCTOR'S INSTRUCTIONS ==
Look at the conversation history above. If the Doctor (nutritionist) has given specific instructions about how to handle certain questions, you MUST follow those instructions. For example:
- If Doctor said "tell them yes they can eat X twice a week" → When client asks about X, say YES according to the doctor's instruction
- If Doctor said "contact me when they ask about Y" → Escalate only that specific question
- If Doctor gave any specific guidance → Follow it exactly

Do NOT escalate questions that the Doctor has already answered in the conversation history.

== YOUR TASK ==
Read the client's new message carefully and respond with ONLY a valid JSON object. No extra text before or after.

{{
  "action": "handle" or "escalate",
  "adherence": "on_track" or "partial" or "off_track" or null,
  "energy_level": 1-5 or null,
  "reply": "Your warm, supportive reply to the client here",
  "escalation_reason": "Clinical reason for escalating (only if action is escalate)"
}}

== ESCALATION RULES — You MUST set action=escalate if ANY of these are true ==
1. Client reports physical pain, dizziness, nausea, cramps, or ANY physical symptom
2. Client asks to substitute a major meal component or change their macros/protein/carbs
3. Client asks a medication-related question
4. Client mentions a medical emergency
5. Client's message contradicts a specific medical constraint in the rules above
6. BUT: If the Doctor has already answered this question in the conversation history, do NOT escalate again — answer based on Doctor's instruction

== WHEN ESCALATING ==
Set reply to a warm interim message ONLY. Example:
"I understand! I've shared this with {nutritionist['full_name']} — she will respond shortly."

== ADHERENCE CLASSIFICATION GUIDE ==
on_track   → Client followed all planned meals and activities
partial    → Client followed some meals/habits but skipped others
off_track  → Client significantly deviated from the plan
null       → Message is a question or not a check-in reply (don't classify)

== ENERGY LEVEL GUIDE ==
Extract energy level ONLY if client mentions it (1=very low, 5=very high). Set null if not mentioned.

Always be warm, encouraging, and empathetic. Use the client's first name. Keep replies concise (2-4 lines max).
"""


def evaluate(client: dict, nutritionist: dict, rules_text: str, history_text: str, new_message: str) -> dict:
    """
    Main function: sends message to Gemini and returns a structured decision.

    Returns dict with keys:
    - action: 'handle' or 'escalate'
    - adherence: 'on_track', 'partial', 'off_track', or None
    - energy_level: int 1-5 or None
    - reply: str — message to send to client
    - escalation_reason: str or None
    """
    system_prompt = build_system_prompt(client, nutritionist, rules_text, history_text)
    full_prompt = f"{system_prompt}\n\n== NEW CLIENT MESSAGE ==\n{client['full_name']}: {new_message}"

    try:
        response = _model.generate_content(full_prompt)
        raw_text = response.text.strip()

        # Strip markdown code block if Gemini wraps in ```json ... ```
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        result = json.loads(raw_text)

        # Validate and normalize the response
        return {
            "action": result.get("action", "handle"),
            "adherence": result.get("adherence"),
            "energy_level": result.get("energy_level"),
            "reply": result.get("reply", "Thanks for sharing! I'll let Dr. know. 😊"),
            "escalation_reason": result.get("escalation_reason"),
        }

    except json.JSONDecodeError:
        # If Gemini returns something unparseable, default to a safe escalation
        logger.warning("Gemini returned non-JSON response. Defaulting to escalation.")
        return {
            "action": "escalate",
            "adherence": None,
            "energy_level": None,
            "reply": "Thanks for sharing! I've flagged this for the doctor to review. 👩‍⚕️",
            "escalation_reason": "AI returned unparseable response — safe escalation applied.",
        }

    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return {
            "action": "escalate",
            "adherence": None,
            "energy_level": None,
            "reply": "I'm having a small issue right now. I've notified the doctor! 🙏",
            "escalation_reason": f"API error: {str(e)}",
        }


def generate_weekly_summary(client: dict, nutritionist: dict, weekly_stats: dict, checkins: list) -> str:
    """
    Generates a weekly progress summary message for the client's Telegram group.
    Called every Sunday by the scheduler.
    """
    prompt = f"""You are NutriCoach AI. Write a warm, encouraging weekly summary for {client['full_name']}'s Telegram group.

Client: {client['full_name']}
Program: {client.get('program_type', 'Nutrition Program')}
Doctor: {nutritionist['full_name']}

This week's stats:
- On Track days: {weekly_stats.get('on_track', 0)}
- Partial days: {weekly_stats.get('partial', 0)}
- Off Track days: {weekly_stats.get('off_track', 0)}
- No Response days: {weekly_stats.get('no_response', 0)}
- Consistency rate: {weekly_stats.get('consistency_pct', 0)}%

Write a 3-4 line summary. Celebrate wins. Gently encourage improvement if needed.
Start with "📊 Weekly Progress — {client['full_name']}!" and end with a motivational note.
Use emoji. Keep it warm and personal. Do not use medical jargon.
"""
    try:
        response = _model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return (
            f"📊 Weekly Progress — {client['full_name']}!\n\n"
            f"You completed {weekly_stats.get('consistency_pct', 0)}% of your check-ins this week. "
            f"Keep going — every day counts! 💪\n\n"
            f"— NutriCoach AI"
        )
