"""
db/ai_rules.py
--------------
All database operations for the ai_rules table.
Rules tell the AI how to behave per client — tone, language, medical constraints etc.
"""

from db.client import supabase
from typing import Optional


def get_master_rules(nutritionist_id: str) -> list:
    """
    Get all rules that apply to ALL clients of this nutritionist.
    These are the base instructions regardless of which client is being handled.
    (client_id is NULL for master rules)
    """
    res = (
        supabase.table("ai_rules")
        .select("*")
        .eq("nutritionist_id", nutritionist_id)
        .is_("client_id", "null")
        .eq("is_active", True)
        .execute()
    )
    return res.data or []


def get_client_rules(client_id: str) -> list:
    """
    Get all rules specific to one client.
    These are layered ON TOP of the master rules.
    """
    res = (
        supabase.table("ai_rules")
        .select("*")
        .eq("client_id", client_id)
        .eq("is_active", True)
        .execute()
    )
    return res.data or []


def get_all_for_client(nutritionist_id: str, client_id: str) -> list:
    """
    Get ALL rules that apply when talking to a specific client:
    master rules + client-specific rules combined.
    """
    master = get_master_rules(nutritionist_id)
    client_specific = get_client_rules(client_id)
    return master + client_specific


def create(
    nutritionist_id: str,
    rule_text: str,
    category: str,
    client_id: Optional[str] = None,
) -> dict:
    """
    Add a new AI rule.
    - If client_id is None → master rule (applies to all clients)
    - If client_id is set → rule specific to that client only
    category: 'tone', 'language', 'medical', 'caretaker', 'other'
    """
    res = supabase.table("ai_rules").insert({
        "nutritionist_id": nutritionist_id,
        "client_id": client_id,
        "category": category,
        "rule_text": rule_text,
        "is_active": True,
    }).execute()
    return res.data[0]


def deactivate(rule_id: str) -> dict:
    """Soft-delete a rule by marking it inactive (not a hard delete)."""
    res = (
        supabase.table("ai_rules")
        .update({"is_active": False})
        .eq("id", rule_id)
        .execute()
    )
    return res.data[0] if res.data else {}


def format_rules_for_prompt(rules: list) -> str:
    """
    Format rules list into a readable bullet-point string for the AI system prompt.
    """
    if not rules:
        return "No special rules set."

    category_labels = {
        "tone": "🗣️ Tone & Style",
        "language": "🌐 Language",
        "medical": "🚫 Medical Constraints",
        "caretaker": "👨‍👩‍👧 Caretaker",
        "other": "📋 Other",
    }

    grouped: dict = {}
    for rule in rules:
        cat = rule.get("category", "other")
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(rule["rule_text"])

    lines = []
    for cat, rule_texts in grouped.items():
        label = category_labels.get(cat, cat.title())
        lines.append(f"{label}:")
        for text in rule_texts:
            lines.append(f"  • {text}")

    return "\n".join(lines)
