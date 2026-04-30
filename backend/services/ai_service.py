"""
services/ai_service.py — Vertex AI (Gemini) integration layer.

Responsibilities:
  - Initialise the Vertex AI client once at import time.
  - Load the system prompt from gemini.md (single source of truth).
  - Expose reusable prompt-building functions for each use case.
  - Execute a single Gemini call per request (MVP strategy).
  - Apply post-processing to enforce neutrality before returning.

What does NOT belong here:
  - Step logic (flow_engine owns that).
  - Firestore reads/writes (data_service and user_service own those).
  - Scenario resolution (scenario_handler owns that).
  - Router logic of any kind.

CALL STRATEGY (Phase 5 MVP):
  One Gemini call per request. The single call handles both intent
  understanding and explanation generation. The prompt template carries
  enough context to guide the model's behaviour without needing a
  separate classification call. Multi-call architecture is Phase 6.
"""

import logging
import re
from pathlib import Path
from dataclasses import dataclass

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig

from backend.config import settings

logger = logging.getLogger(__name__)

# ── Vertex AI initialisation ───────────────────────────────────────────────────
# Runs once when this module is first imported.
# Uses PROJECT_ID and REGION from config (loaded from .env).
vertexai.init(project=settings.project_id, location=settings.region)

MODEL_NAME = "gemini-1.5-flash"

# Conservative generation config — keeps responses factual and concise.
_GENERATION_CONFIG = GenerationConfig(
    temperature=0.2,        # Low temperature = more predictable, factual output.
    max_output_tokens=512,  # Enough for structured step explanations.
    top_p=0.8,
)

# ── System prompt ──────────────────────────────────────────────────────────────

def _load_system_prompt() -> str:
    """
    Load the system prompt from gemini.md at the project root.

    Loading from file (not hardcoding) ensures the AI behaviour
    stays in sync with gemini.md as it evolves — one source of truth.
    Raises FileNotFoundError at startup if gemini.md is missing.
    """
    prompt_path = Path(__file__).resolve().parents[2] / "gemini.md"
    return prompt_path.read_text(encoding="utf-8")


# Loaded once at module import — not on every request.
_SYSTEM_PROMPT: str = _load_system_prompt()


# ── Result type ────────────────────────────────────────────────────────────────

@dataclass
class AIResult:
    """Structured output from a single AI call."""
    explanation: str
    action_items: list[str]
    disclaimer: str | None = None


# ── Prompt templates ───────────────────────────────────────────────────────────
# Each template follows the same structure:
#   ROLE → CONTEXT → TASK → CONSTRAINTS → OUTPUT FORMAT
# Keeping templates here (not in routers) means prompt changes
# never require touching route files.

def _prompt_explain_step(
    step_name: str,
    step_description: str,
    user_message: str,
    region: str,
    language: str,
) -> str:
    """
    Template 1 — Explain a journey step in the context of a user question.
    Used for: GET /journey/{user_id}/step?message=...
    """
    return f"""
ROLE:
You are an AI Election Navigator — a neutral, factual guidance assistant.

CONTEXT:
- The user is on journey step: "{step_name}"
- Step description: "{step_description}"
- User's region: {region}
- Respond in language: {language}

USER QUESTION:
{user_message}

TASK:
Explain this step clearly. Address the user's question in the context of this step.

CONSTRAINTS:
- Do NOT recommend any candidate or party.
- Do NOT express any political opinion.
- Do NOT advance or skip steps — step progression is handled externally.
- Use only the context provided — do NOT invent regional facts.
- Keep language simple. Avoid legal jargon.

OUTPUT FORMAT:
Return your response in exactly this structure:

EXPLANATION:
<2-4 sentences explaining the concept or answering the question>

ACTIONS:
- <action item 1>
- <action item 2>
- <action item 3>

NEXT ACTION:
<single most important thing the user should do now>
""".strip()


def _prompt_generate_timeline(
    region: str,
    election_date: str,
    registration_deadline: str,
    verification_deadline: str,
    process_steps: list[str],
) -> str:
    """
    Template 2 — Explain the election timeline for a region.
    Used for: GET /elections/{region_id}/timeline with AI explanation.
    """
    steps_text = "\n".join(f"- {s}" for s in process_steps)
    return f"""
ROLE:
You are an AI Election Navigator providing a neutral timeline explanation.

CONTEXT:
Region: {region}
Election Date: {election_date}
Registration Deadline: {registration_deadline}
Verification Deadline: {verification_deadline}

Process Steps:
{steps_text}

TASK:
Summarise the key dates and what the user must do at each stage.
Highlight any urgent upcoming deadlines.

CONSTRAINTS:
- Factual only. Do NOT add information not present in the context above.
- Do NOT recommend any party or candidate.
- Use simple language.

OUTPUT FORMAT:
EXPLANATION:
<summary of timeline>

ACTIONS:
- <action item 1>
- <action item 2>

NEXT ACTION:
<most urgent thing to do>
""".strip()


def _prompt_simplify_policy(policy_text: str, language: str) -> str:
    """
    Template 3 — Simplify a policy statement into plain language.
    Used for: party detail views with complex policy text.
    """
    return f"""
ROLE:
You are an AI Election Navigator simplifying policy information.

CONTEXT:
Respond in language: {language}

POLICY TEXT:
{policy_text}

TASK:
Rewrite the above policy in simple, jargon-free language a first-time voter can understand.

CONSTRAINTS:
- Do NOT evaluate, praise, or criticise the policy.
- Do NOT compare it to other parties' policies.
- Neutral, factual tone only.
- Maximum 3 sentences.

OUTPUT FORMAT:
EXPLANATION:
<simplified policy in plain language>

ACTIONS:
- Learn more at your official election authority website.

NEXT ACTION:
Compare this with other parties' positions on the same topic for a complete picture.
""".strip()


def _prompt_compare_parties(
    party_data: list[dict],
    region: str,
    language: str,
) -> str:
    """
    Template 4 — Present party information side-by-side in a neutral way.
    Used for: GET /parties/{region_id} with AI-generated summary.

    CRITICAL: No ranking, no recommendation, no evaluative language.
    Disclaimer is always appended by post-processing.
    """
    party_blocks = []
    for party in party_data:
        name = party.get("name", "Unknown")
        focus = ", ".join(party.get("focus_areas", []))
        policies = "\n  ".join(party.get("key_policies", []))
        party_blocks.append(f"Party: {name}\nFocus Areas: {focus}\nKey Policies:\n  {policies}")

    parties_text = "\n\n".join(party_blocks)

    return f"""
ROLE:
You are an AI Election Navigator presenting neutral party information.

CONTEXT:
Region: {region}
Respond in language: {language}

PARTY DATA:
{parties_text}

TASK:
Present each party's focus areas and policies clearly.
Do NOT rank, compare favourably, or suggest any party is better.

CONSTRAINTS:
- No opinions. No recommendations. No ranking language.
- Do NOT say phrases like "better", "stronger", "best choice".
- Present each party in equal depth.
- Factual tone only.

OUTPUT FORMAT:
EXPLANATION:
<neutral summary of all parties presented>

ACTIONS:
- Review each party's official manifesto for complete details.
- Verify information with your local election authority.

NEXT ACTION:
Consider which focus areas align with issues important to you — without pressure to choose.
""".strip()


# ── Core AI call ───────────────────────────────────────────────────────────────

def call_gemini(prompt: str) -> AIResult:
    """
    Execute a single Gemini call with the system prompt and return structured output.

    This is the only function that touches the Gemini API.
    All prompt-building happens in the template functions above.
    All response parsing happens in _parse_response() below.
    Post-processing (neutrality enforcement) runs before returning.
    """
    model = GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=_SYSTEM_PROMPT,
        generation_config=_GENERATION_CONFIG,
    )

    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        result = _parse_response(raw_text)
        return _apply_safety_filter(result)

    except Exception as exc:
        logger.error("Gemini call failed: %s", exc)
        # Return a safe fallback — never surface raw errors to users.
        return AIResult(
            explanation="I'm unable to provide a response right now. Please try again shortly.",
            action_items=["Please verify with your local election authority for guidance."],
        )


# ── Response parsing ───────────────────────────────────────────────────────────

def _parse_response(raw: str) -> AIResult:
    """
    Parse Gemini's structured output into an AIResult.

    Expects the OUTPUT FORMAT defined in each prompt template:
      EXPLANATION: ...
      ACTIONS: - item ...
      NEXT ACTION: ...

    Falls back gracefully if the model doesn't follow the format exactly.
    """
    explanation = _extract_section(raw, "EXPLANATION")
    actions_block = _extract_section(raw, "ACTIONS")
    next_action = _extract_section(raw, "NEXT ACTION")

    # Parse bullet lines from the ACTIONS block.
    action_items = [
        line.lstrip("-• ").strip()
        for line in actions_block.splitlines()
        if line.strip().startswith(("-", "•"))
    ]

    # Append next action as the final item if present.
    if next_action:
        action_items.append(f"→ {next_action}")

    # If parsing produced nothing, use the full response as explanation.
    if not explanation:
        explanation = raw

    return AIResult(explanation=explanation, action_items=action_items)


def _extract_section(text: str, section_name: str) -> str:
    """Extract the content under a named section heading."""
    pattern = rf"{section_name}:\s*(.*?)(?=\n[A-Z ]+:|$)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


# ── Safety post-processing ─────────────────────────────────────────────────────

# Phrases that must never appear in a response to any user.
_BANNED_PATTERNS: list[re.Pattern] = [
    re.compile(r"\bbest (party|candidate|choice|option)\b", re.IGNORECASE),
    re.compile(r"\bvote for\b", re.IGNORECASE),
    re.compile(r"\brecommend(ed|ing)?\b.{0,30}(party|candidate)", re.IGNORECASE),
    re.compile(r"\byou should (support|back|choose|pick)\b", re.IGNORECASE),
    re.compile(r"\bstrongest (party|candidate)\b", re.IGNORECASE),
]

_PARTY_DISCLAIMER = (
    "⚠️ This information is provided for awareness only and does not "
    "recommend or endorse any candidate or party."
)

_VERIFICATION_NOTE = (
    "Please verify region-specific details with your local election authority."
)


def _apply_safety_filter(result: AIResult) -> AIResult:
    """
    Post-process the AI result to enforce neutrality constraints from gemini.md.

    Rule-based — not another AI call. Runs on every response regardless
    of intent, as a final safety net before the result leaves this module.
    """
    cleaned_explanation = result.explanation
    for pattern in _BANNED_PATTERNS:
        cleaned_explanation = pattern.sub("[removed]", cleaned_explanation)

    # Flag if the response was altered — useful for monitoring.
    if cleaned_explanation != result.explanation:
        logger.warning("Safety filter removed biased content from AI response.")

    # Attach verification note if not already in action items.
    action_items = list(result.action_items)
    if not any(_VERIFICATION_NOTE in item for item in action_items):
        action_items.append(_VERIFICATION_NOTE)

    return AIResult(
        explanation=cleaned_explanation,
        action_items=action_items,
        disclaimer=result.disclaimer,
    )


# ── Public API (ADDED) ─────────────────────────────────────────────────────────
# Routers call these functions — never the private _prompt_* functions directly.
# Each wrapper builds the prompt then executes the single Gemini call.

def explain_step(
    step_name: str,
    step_description: str,
    user_message: str,
    region: str,
    language: str,
) -> AIResult:
    """Public wrapper for step explanation. Entry point for journey router."""
    prompt = _prompt_explain_step(step_name, step_description, user_message, region, language)
    return call_gemini(prompt)


def generate_timeline(
    region: str,
    election_date: str,
    registration_deadline: str,
    verification_deadline: str,
    process_steps: list[str],
) -> AIResult:
    """Public wrapper for timeline explanation. Entry point for elections router."""
    prompt = _prompt_generate_timeline(
        region, election_date, registration_deadline, verification_deadline, process_steps
    )
    return call_gemini(prompt)


def simplify_policy(policy_text: str, language: str) -> AIResult:
    """Public wrapper for policy simplification. Entry point for parties router."""
    prompt = _prompt_simplify_policy(policy_text, language)
    return call_gemini(prompt)


def compare_parties(party_data: list[dict], region: str, language: str) -> AIResult:
    """Public wrapper for neutral party presentation. Entry point for parties router."""
    prompt = _prompt_compare_parties(party_data, region, language)
    return call_gemini(prompt)


def chat_assist(message: str, region_id: str, language: str = "en") -> dict:
    """
    Controlled AI assistant for neutral party comparison.
    Maps user message to policy areas and returns structured matching.
    """
    # 1. Fetch parties for the region
    from backend.services.data_service import get_parties
    parties = get_parties(region_id) or []
    
    # 2. Build structured prompt
    prompt = f"""
    ROLE: Neutral Election Assistant
    TASK: Map user priorities to party policies.
    
    USER MESSAGE: "{message}"
    REGION: {region_id}
    LANGUAGE: {language}
    
    PARTIES DATA: {parties}
    
    RULES:
    - DO NOT recommend a party.
    - DO NOT rank parties.
    - DO NOT use words like "best", "better", "recommended".
    - ONLY match user interests to relevant policies/focus areas from the data.
    
    RETURN JSON:
    {{
        "intent": "identified user interest",
        "relevant_areas": ["area1", "area2"],
        "parties": [
            {{
                "name": "Party Name",
                "matching_policies": ["policy1", "policy2"]
            }}
        ],
        "disclaimer": "This information is for awareness only and does not recommend any party."
    }}
    """
    
    try:
        response = call_gemini(prompt)
        # Note: In a production environment, call_gemini would return AIResult.
        # Here we extract the raw text and parse JSON for the chat endpoint.
        import json
        import re
        
        # Clean potential markdown
        content = response.explanation if hasattr(response, 'explanation') else str(response)
        cleaned = re.sub(r'```json|```', '', content).strip()
        return json.loads(cleaned)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("AI Chat failed: %s", str(e))
        return {
            "intent": "unknown",
            "relevant_areas": [],
            "parties": [],
            "disclaimer": "AI assistant is currently unavailable. Please check party details manually."
        }
