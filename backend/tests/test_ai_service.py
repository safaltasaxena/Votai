import pytest
from backend.services.ai_service import keyword_fallback

# Sample data for testing
MOCK_PARTIES = [
    {"name": "Health Plus", "focus_areas": ["Healthcare", "Women"]},
    {"name": "EduTech", "focus_areas": ["Education", "Digital"]},
    {"name": "Green Road", "focus_areas": ["Infrastructure", "Environment"]},
    {"name": "Future Jobs", "focus_areas": ["Employment", "Youth"]},
    {"name": "Digital India", "focus_areas": ["Digital", "Economy"]},
]

def test_healthcare_match():
    """Verify exact and synonym matching for healthcare."""
    res = keyword_fallback("I care about hospitals and health", MOCK_PARTIES)
    msg = res["message"].lower()
    assert "healthcare" in msg
    assert "health plus" in msg
    assert res["status"] == "fallback"

def test_multi_category_match():
    """Verify system detects two categories when relevant."""
    res = keyword_fallback("Tell me about schools and roads", MOCK_PARTIES)
    # Should detect education and infrastructure
    msg = res["message"].lower()
    assert "education" in msg
    assert "infrastructure" in msg
    assert "edutech" in msg
    assert "green road" in msg

def test_no_keyword_general():
    """Verify general overview triggers when no keywords match."""
    res = keyword_fallback("random gibberish", MOCK_PARTIES)
    msg = res["message"].lower()
    assert "overview of major parties" in msg
    assert "health plus" in msg
    assert res["status"] == "fallback"

def test_partial_match():
    """Verify substring matching works for keywords."""
    # 'internet' is a keyword for 'digital'
    res = keyword_fallback("I want better internets", MOCK_PARTIES)
    msg = res["message"].lower()
    assert "digital" in msg
    assert "edutech" in msg or "digital india" in msg

def test_empty_parties():
    """Verify safe handling of empty party list."""
    res = keyword_fallback("healthcare", [])
    msg = res["message"].lower()
    assert "currently being updated" in msg

def test_compare_intent():
    """Verify intent detection for comparisons."""
    res = keyword_fallback("compare the parties on jobs", MOCK_PARTIES)
    msg = res["message"].lower()
    assert "comparison" in msg
    assert "employment" in msg
    assert "future jobs" in msg
