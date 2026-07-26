"""
ai/gemini.py — All Gemini API calls live here.

Two main functions:
  1. generate_reply()    → natural-language response to post in Telegram
  2. extract_checkin()   → structured JSON extracted from client's reply
  3. generate_checkin_question() → personalized daily or weekly question

All calls include the full conversation history for that client.
Failed calls are retried once before raising.
"""

import json
import time
import logging
from typing import Optional

from google import genai
from google.genai import types

import config
from db.models import Client, Message, CheckIn
from ai.prompts import (
    build_system_prompt,
    build_conversation_context,
    EXTRACTION_SYSTEM_PROMPT,
    EXTRACTION_SCHEMA,
    DAILY_QUESTION_PROMPT,
    WEEKLY_QUESTION_PROMPT,
)

logger = logging.getLogger(__name__)

# Initialise the Gemini client once at import time
_client = genai.Client(api_key=config.GEMINI_API_KEY)


def _call_gemini_with_retry(
    contents: list,
    system_instruction: str,
    response_mime_type: str = "text/plain",
    response_schema=None,
    max_retries: int = 2,
) -> str:
    """
    Internal helper: call Gemini with automatic retry on failure.
    Returns the text of the first candidate.
    """
    generate_config_kwargs = {
        "system_instruction": system_instruction,
        "response_mime_type": response_mime_type,
    }
    if response_schema is not None:
        generate_config_kwargs["response_schema"] = response_schema

    generate_config = types.GenerateContentConfig(**generate_config_kwargs)

    last_error = None
    for attempt in range(max_retries):
        try:
            response = _client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=contents,
                config=generate_config,
            )
            return response.text
        except Exception as e:
            last_error = e
            logger.warning(
                f"[GEMINI] Attempt {attempt + 1}/{max_retries} failed: {e}"
            )
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # exponential back-off: 1s, 2s

    raise RuntimeError(
        f"[GEMINI] All {max_retries} attempts failed. Last error: {last_error}"
    )


# ── 1. Generate natural-language reply ───────────────────────────────────────

def generate_reply(
    client: Client,
    recent_messages: list[Message],
    new_message: str,
    sender_role: str,
) -> str:
    """
    Generate a warm, coach-like reply to post back in the Telegram group.

    Args:
        client:          The client record (for their plan + name).
        recent_messages: Last N messages from DB (conversation history).
        new_message:     The incoming message text.
        sender_role:     'customer' | 'caretaker'

    Returns:
        A natural-language string to send to the Telegram group.
    """
    system_prompt = build_system_prompt(client, config.COACH_NAME)

    # Build conversation history as Gemini content turns
    contents = build_conversation_context(recent_messages)

    # Append the new incoming message
    role_label = "Client" if sender_role == "customer" else "Caretaker"
    contents.append({
        "role": "user",
        "parts": [{"text": f"[{role_label}]: {new_message}"}],
    })

    logger.info(f"[GEMINI] Generating reply for client '{client.name}' ({sender_role})")

    reply = _call_gemini_with_retry(
        contents=contents,
        system_instruction=system_prompt,
        response_mime_type="text/plain",
    )

    return reply.strip()


# ── 2. Extract structured check-in data ──────────────────────────────────────

def extract_checkin(
    client: Client,
    recent_messages: list[Message],
    new_message: str,
    sender_role: str,
) -> dict:
    """
    Extract structured JSON from a client's/caretaker's check-in reply.

    Returns a dict with keys: adherence, energy_level, mood, symptoms,
    caretaker_note, needs_attention, flag_reason, summary.
    On parse failure, returns a safe fallback dict.
    """
    system_prompt = EXTRACTION_SYSTEM_PROMPT + f"\n\nClient name: {client.name}\nClient plan: {client.plan_summary}"

    # Include recent history + new message for context
    contents = build_conversation_context(recent_messages)
    role_label = "Client" if sender_role == "customer" else "Caretaker"
    contents.append({
        "role": "user",
        "parts": [{"text": f"[{role_label}]: {new_message}\n\nNow extract the structured data from the above reply."}],
    })

    logger.info(f"[GEMINI] Extracting check-in data for client '{client.name}'")

    try:
        raw = _call_gemini_with_retry(
            contents=contents,
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=EXTRACTION_SCHEMA,
        )
        # Gemini JSON mode returns a string — parse it
        data = json.loads(raw)
        return data
    except (json.JSONDecodeError, RuntimeError) as e:
        logger.error(f"[GEMINI] Extraction failed for '{client.name}': {e}")
        # Safe fallback — don't lose the check-in entirely
        return {
            "adherence": "unclear",
            "energy_level": "not_mentioned",
            "mood": None,
            "symptoms": [],
            "caretaker_note": None,
            "needs_attention": False,
            "flag_reason": None,
            "summary": f"[Auto-extraction failed] Raw: {new_message[:200]}",
        }


# ── 3. Generate personalised check-in question ───────────────────────────────

def generate_checkin_question(
    client: Client,
    checkin_type: str,
    recent_messages: list[Message],
    recent_checkins: list[CheckIn] = None,
) -> str:
    """
    Generate a personalised daily or weekly check-in question for a client.

    Args:
        client:          The client record.
        checkin_type:    'daily' | 'weekly'
        recent_messages: Recent conversation history.
        recent_checkins: Recent structured check-in records (for weekly).

    Returns:
        The question string to send to the Telegram group.
    """
    system_prompt = build_system_prompt(client, config.COACH_NAME)

    # Build context
    contents = build_conversation_context(recent_messages)

    # Add check-in history summary for weekly questions
    if checkin_type == "weekly" and recent_checkins:
        checkin_summary_lines = []
        for ci in recent_checkins:
            checkin_summary_lines.append(
                f"- Date: {ci.created_at.strftime('%Y-%m-%d')} | "
                f"Adherence: {ci.adherence} | Energy: {ci.energy_level} | "
                f"Summary: {ci.summary or 'N/A'}"
            )
        summary_text = "\n".join(checkin_summary_lines)
        contents.append({
            "role": "user",
            "parts": [{"text": f"[SYSTEM] Recent check-in history for this client:\n{summary_text}"}],
        })

    question_prompt = DAILY_QUESTION_PROMPT if checkin_type == "daily" else WEEKLY_QUESTION_PROMPT
    contents.append({
        "role": "user",
        "parts": [{"text": question_prompt}],
    })

    logger.info(
        f"[GEMINI] Generating {checkin_type} question for client '{client.name}'"
    )

    question = _call_gemini_with_retry(
        contents=contents,
        system_instruction=system_prompt,
        response_mime_type="text/plain",
    )

    return question.strip()
