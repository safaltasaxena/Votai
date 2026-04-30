"""
services/scenario_handler.py — Pre-defined resolutions for real-world edge cases.

ARCHITECTURE RULE:
  Routers must check scenario_handler BEFORE any AI call.
  If a scenario is matched, return the static resolution directly —
  do not forward the request to ai_service.

Why static responses (no AI)?
  These are critical, high-stakes situations (e.g. name not on voter list).
  Hallucinated steps could cause a user to miss their chance to vote.
  Static, verified steps are safer than AI-generated ones for these cases.

Responsibilities:
  - Detect whether a user message matches a known scenario.
  - Return a pre-verified, structured resolution for matched scenarios.
  - Return None when no scenario is matched (AI call proceeds normally).
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScenarioResolution:
    """
    Immutable resolution for a single edge-case scenario.

    frozen=True prevents accidental mutation after construction.
    """
    scenario_key: str
    title: str
    steps: list[str]
    fallback_note: str


# ── Scenario registry ──────────────────────────────────────────────────────────
# Add new scenarios here only. One entry per known edge case.
# Steps must be verified against official processes before adding.

_SCENARIOS: dict[str, ScenarioResolution] = {
    "moved_city": ScenarioResolution(
        scenario_key="moved_city",
        title="You've moved to a new city or state",
        steps=[
            "Visit your new state's official voter registration portal.",
            "Submit a change-of-address form (Form 8A in India, or equivalent in your region).",
            "Provide proof of new address (utility bill, rental agreement, etc.).",
            "Check whether the registration deadline has passed — if so, ask about provisional voting.",
            "Collect your updated Voter ID from the local BLO (Booth Level Officer) office.",
        ],
        fallback_note=(
            "Registration rules vary by state. "
            "Please verify the exact process with your new local election authority."
        ),
    ),

    "missed_registration": ScenarioResolution(
        scenario_key="missed_registration",
        title="You missed the voter registration deadline",
        steps=[
            "Confirm the exact deadline on the official election commission website for your region.",
            "Ask your local election office whether same-day or late registration is available.",
            "If registration is fully closed for this election, note the next election cycle's dates.",
            "Set a calendar reminder for the next registration window opening.",
        ],
        fallback_note=(
            "Deadlines and late-registration options vary by region. "
            "Always verify with your official election authority."
        ),
    ),

    "name_not_found": ScenarioResolution(
        scenario_key="name_not_found",
        title="Your name is missing from the voter list",
        steps=[
            "Search the official voter list portal using alternative spellings of your name.",
            "Visit your local election office with your registration receipt and a valid ID.",
            "File a formal grievance using Form 6 (India) or the equivalent form in your region.",
            "Request a written acknowledgement of your complaint from the office.",
            "Follow up 7–10 days before election day to confirm the correction has been made.",
        ],
        fallback_note=(
            "Bring all available proof of registration (receipt, ID, address proof). "
            "Contact your local election authority immediately — time-sensitive."
        ),
    ),
}

# Keywords that indicate each scenario. Matched case-insensitively.
_KEYWORDS: dict[str, list[str]] = {
    "moved_city":           ["moved", "new city", "new state", "relocated", "shifted", "transfer"],
    "missed_registration":  ["missed", "deadline", "too late", "registration closed", "expired"],
    "name_not_found":       ["not found", "missing", "not on list", "not in list", "not appear", "name missing"],
}


def detect_scenario(user_message: str) -> str | None:
    """
    Check whether a user message matches a known scenario key.

    Returns the matching scenario key, or None if no match is found.
    Matching is keyword-based and case-insensitive — intentionally simple
    to avoid false positives on ambiguous phrasing.
    """
    lowered = user_message.lower()

    for scenario_key, keywords in _KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return scenario_key

    return None


def resolve(scenario_key: str) -> ScenarioResolution | None:
    """
    Return the pre-defined resolution for a known scenario key.

    Returns None for unrecognised keys — callers should treat this
    as "no scenario matched, proceed to AI".
    """
    return _SCENARIOS.get(scenario_key)


def handle(user_message: str) -> ScenarioResolution | None:
    """
    Convenience function: detect and resolve in one call.

    Returns a ScenarioResolution if a scenario is matched,
    or None if the message should be forwarded to the AI service.

    Routers should call this first on every /chat request.
    """
    scenario_key = detect_scenario(user_message)
    if scenario_key is None:
        return None
    return resolve(scenario_key)
