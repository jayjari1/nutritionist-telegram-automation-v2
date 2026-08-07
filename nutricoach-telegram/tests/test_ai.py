"""
tests/test_ai.py
----------------
Tests for AI pipeline functions.
"""

import os
import pytest


def test_gemini_imports():
    """Check that Gemini module can be imported."""
    from ai.gemini import evaluate
    assert callable(evaluate)


def test_router_imports():
    """Check that router module can be imported."""
    from ai.router import route
    assert callable(route)


def test_gemini_evaluate_returns_dict():
    """Check that Gemini evaluate returns expected structure."""
    from ai.gemini import evaluate
    
    # Mock data
    client = {
        "full_name": "Test Client",
        "program_type": "General Nutrition",
        "diet_chart": "Eat healthy",
    }
    nutritionist = {
        "full_name": "Dr. Test",
        "clinic_name": "Test Clinic",
    }
    rules_text = "Be supportive and encouraging."
    history_text = "Client: I ate healthy today\nAI: Great job!"
    new_message = "I had rice and dal for lunch"
    
    # This will fail if GEMINI_API_KEY is not set
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not set")
    
    result = evaluate(client, nutritionist, rules_text, history_text, new_message)
    
    assert isinstance(result, dict)
    assert "action" in result
    assert "reply" in result
    assert result["action"] in ["handle", "escalate"]
