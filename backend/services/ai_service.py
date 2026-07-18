"""
services/ai_service.py — OpenAI integration layer.

Responsibilities:
  - Initialise the OpenAI client once at import time.
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
from dataclasses import dataclass
from pathlib import Path




from ai.ai_client import generate_content

logger = logging.getLogger(__name__)

# ── OpenAI initialisation ───────────────────────────────────────────────────
# Runs once when this module is first imported.


# Conservative generation config — keeps responses factual and concise.


# ── System prompt ──────────────────────────────────────────────────────────────

def _load_system_prompt() -> str:
    try:
        from pathlib import Path

        # 🔥 try multiple safe paths
        possible_paths = [
            Path(__file__).resolve().parent.parent / "ai" / "openai.md",
            Path("backend/ai/openai.md"),
        ]

        for path in possible_paths:
            if path.exists():
                return path.read_text(encoding="utf-8")

        print("⚠️ openai.md not found — using fallback prompt")
        return "You are a neutral civic assistant."

    except Exception as e:
        print("⚠️ Failed loading openai.md:", e)
        return "You are a neutral civic assistant."


# Loaded once at module import — not on every request.
_SYSTEM_PROMPT: str = _load_system_prompt()


# ── Result type ────────────────────────────────────────────────────────────────

@dataclass
class AIResult:
    """Structured output from a single AI call."""
    explanation: str
    action_items: list[str]
    disclaimer: str | None = None
    status: str = "success"


# ── Prompt templates ───────────────────────────────────────────────────────────

def _prompt_chat_assist(message: str, context: str, language: str) -> str:
    """Template 5 — Answer general civic queries with party context."""
    return f"""
ROLE:
You are an AI Election Navigator — a neutral, factual assistant.

CONTEXT:
Respond in language: {language}
Relevant Party Data:
{context}

USER QUERY:
{message}

TASK:
Provide a neutral, factual answer or comparison based ONLY on the provided party data.

CONSTRAINTS:
- DO NOT recommend any party or candidate.
- DO NOT rank parties or use words like "better", "best", "strongest".
- If comparing, use bullet points and give equal weight to each party.
- Keep the tone helpful but clinical.
- If the user asks for a recommendation, politely decline and explain your neutrality.

OUTPUT FORMAT:
EXPLANATION:
<your neutral answer or comparison>

ACTIONS:
- <action item 1>
- <action item 2>

NEXT ACTION:
<single most important thing for the user to do>
""".strip()


def _prompt_explain_step(
    step_name: str,
    step_description: str,
    user_message: str,
    region: str,
    language: str,
) -> str:
    """Template 1 — Explain a journey step in the context of a user question."""
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
    """Template 2 — Explain the election timeline for a region."""
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
    """Template 3 — Simplify a policy statement into plain language."""
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
    """Template 4 — Present party information side-by-side in a neutral way."""
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

def _prompt_generate_timeline(
    region: str,
    election_date: str,
    registration_deadline: str,
    verification_deadline: str,
    process_steps: list[str],
) -> str:
    """Template 2 — Explain the election timeline for a region."""
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
    """Template 3 — Simplify a policy statement into plain language."""
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
    """Template 4 — Present party information side-by-side in a neutral way."""
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

def call_ai(prompt: str) -> AIResult:
    """
    Execute an AI call using OpenRouter/OpenAI.
    """

   

    try:
        raw_text = generate_content(
            user_prompt=prompt,
            system_prompt=_SYSTEM_PROMPT,
        ).strip()
    except Exception as e:
        logger.error("AI model failed: %s", e)

        return AIResult(
            explanation="",
            action_items=[],
            status="error"
        )

    result = _parse_response(raw_text)
    return _apply_safety_filter(result)

# ── Response parsing ───────────────────────────────────────────────────────────

def _parse_response(raw: str) -> AIResult:
    """Parse ai's structured output into an AIResult."""
    explanation = _extract_section(raw, "EXPLANATION")
    actions_block = _extract_section(raw, "ACTIONS")
    next_action = _extract_section(raw, "NEXT ACTION")

    action_items = [
        line.lstrip("-• ").strip()
        for line in actions_block.splitlines()
        if line.strip().startswith(("-", "•"))
    ]

    if next_action:
        action_items.append(f"→ {next_action}")

    if not explanation:
        explanation = raw

    return AIResult(explanation=explanation, action_items=action_items)


def _extract_section(text: str, section_name: str) -> str:
    """Extract the content under a named section heading."""
    pattern = rf"{section_name}:\s*(.*?)(?=\n[A-Z ]+:|$)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


# ── Safety post-processing ─────────────────────────────────────────────────────

_BANNED_PATTERNS: list[re.Pattern] = [
    re.compile(r"\bbest (party|candidate|choice|option)\b", re.IGNORECASE),
    re.compile(r"\bvote for\b", re.IGNORECASE),
    re.compile(r"\brecommend(ed|ing)?\b.{0,30}(party|candidate)", re.IGNORECASE),
    re.compile(r"\byou should (support|back|choose|pick)\b", re.IGNORECASE),
    re.compile(r"\bstrongest (party|candidate)\b", re.IGNORECASE),
]

_VERIFICATION_NOTE = (
    "Please verify region-specific details with your local election authority."
)


def _apply_safety_filter(result: AIResult) -> AIResult:
    """Post-process the AI result to enforce neutrality constraints from openai.md."""
    cleaned_explanation = result.explanation
    for pattern in _BANNED_PATTERNS:
        cleaned_explanation = pattern.sub("[removed]", cleaned_explanation)

    if cleaned_explanation != result.explanation:
        logger.warning("Safety filter removed biased content from AI response.")

    action_items = list(result.action_items)
    if not any(_VERIFICATION_NOTE in item for item in action_items):
        action_items.append(_VERIFICATION_NOTE)

    return AIResult(
        explanation=cleaned_explanation,
        action_items=action_items,
        disclaimer=result.disclaimer,
    )


# ── Public API ─────────────────────────────────────────────────────────────────

def explain_step(
    step_name: str,
    step_description: str,
    user_message: str,
    region: str,
    language: str,
) -> AIResult:
    """Public wrapper for step explanation. Entry point for journey router."""
    prompt = _prompt_explain_step(step_name, step_description, user_message, region, language)
    return call_ai(prompt)


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
    return call_ai(prompt)


def simplify_policy(policy_text: str, language: str) -> AIResult:
    """Public wrapper for policy simplification. Entry point for parties router."""
    prompt = _prompt_simplify_policy(policy_text, language)
    return call_ai(prompt)


def compare_parties(party_data: list[dict], region: str, language: str) -> AIResult:
    """Public wrapper for neutral party presentation. Entry point for parties router."""
    prompt = _prompt_compare_parties(party_data, region, language)
    return call_ai(prompt)


# ── Chat Assist ────────────────────────────────────────────────────────────────

def _build_party_context(parties: list) -> str:
    """Format party list into a plain-text block for the AI prompt."""
    blocks = []
    for p in parties:
        blocks.append(
            f"Party: {p.get('name')}\n"
            f"Focus Areas: {', '.join(p.get('focus_areas', []))}\n"
            f"Policies: {', '.join(p.get('key_policies', []))}"
        )
    return "\n---\n".join(blocks)


def keyword_fallback(message: str, parties: list) -> dict:
    """
    Advanced deterministic fallback engine with intent detection 
    and multi-category matching.
    """
    text = message.lower()
    words = text.split()
    
    # 1. Expanded Categories & Synonyms
    keywords_map = {
        "healthcare": ["health", "hospital", "doctor", "medical", "clinic", "wellness", "medicine"],
        "education": ["education", "school", "college", "student", "literacy", "teacher", "learning"],
        "employment": ["jobs", "employment", "career", "work", "unemployment", "hiring"],
        "women": ["women", "female", "safety", "empowerment", "gender"],
        "youth": ["youth", "young", "students", "startup", "skill"],
        "economy": ["economy", "growth", "inflation", "business", "tax", "finance"],
        "infrastructure": ["road", "metro", "transport", "development", "bridge", "connectivity"],
        "digital": ["internet", "digital", "technology", "tech", "online"],
        "agriculture": ["agriculture", "farm", "farmer", "crop", "rural", "krishi"],
    }

    # 2. Weighted Scoring
    scores = {cat: 0 for cat in keywords_map}
    for category, keywords in keywords_map.items():
        for keyword in keywords:
            if keyword in words:
                scores[category] += 3  # Exact word match
            elif keyword in text:
                scores[category] += 1  # Substring match

    # 3. Intent Detection
    is_comparing = any(word in text for word in ["compare", "difference", "vs", "versus"])
    is_seeking_best = any(word in text for word in ["best", "which", "top", "recommend"])

    # Sort categories by score
    sorted_cats = sorted([c for c in scores if scores[c] > 0], key=lambda x: scores[x], reverse=True)
    
    if not sorted_cats:
        return _general_party_overview(parties)

    # 4. Multi-category logic: pick top 2 if scores are close
    selected_cats = [sorted_cats[0]]
    if len(sorted_cats) > 1 and scores[sorted_cats[1]] >= (scores[sorted_cats[0]] * 0.7):
        selected_cats.append(sorted_cats[1])

    # 5. Filter & Rank Parties
    matched_parties = []
    for p in parties:
        p_score = 0
        p_focus_list = [f.lower() for f in p.get("focus_areas", [])]
        p_focus_blob = " ".join(p_focus_list)
        for cat in selected_cats:
            if cat in p_focus_list or cat in p_focus_blob:
                p_score += 1
        if p_score > 0:
            matched_parties.append((p_score, p))
    
    # Sort and take top 3-5
    top_parties = [p for score, p in sorted(matched_parties, key=lambda x: x[0], reverse=True)][:5]

    if not top_parties:
        return _general_party_overview(parties)

    # 6. Natural Language Response Generation
    cat_str = " and ".join(selected_cats)
    header = f"I've analyzed the parties focusing on {cat_str}. "
    
    if is_seeking_best:
        header += "While I cannot recommend a 'best' choice, here are the parties with established policies in these areas:\n\n"
    elif is_comparing:
        header += "Here is a comparison of parties active in these sectors:\n\n"
    else:
        header += "Here are the parties currently prioritizing these issues:\n\n"

    lines = [f"\u2022 {p.get('name')}: {', '.join(p.get('focus_areas', []))}" for p in top_parties]
    
    return {
        "message": header + "\n".join(lines),
        "next_action": "Compare their specific policy documents in the Party Explorer.",
        "status": "fallback"
    }


def _general_party_overview(parties: list) -> dict:
    """Richer general fallback when no keywords match."""
    # Show up to 5 parties
    display_parties = parties[:5]
    lines = [f"\u2022 {p.get('name')}: {', '.join(p.get('focus_areas', []))}" for p in display_parties]
    
    body = "To help you get started, here is an overview of major parties in your region and their primary focus areas:\n\n"
    body += "\n".join(lines) if lines else "Information for this region is currently being updated."
    
    return {
        "message": body,
        "next_action": "Try asking about a specific topic like 'jobs' or 'education'.",
        "status": "fallback"
    }


def chat_assist(message: str, region_id: str, language: str = "en"):
    """
    Answer a user civic query using a 3-layer model:
    1. Scenarios (Deterministic)
    2. AI 
    3. Keyword Match (Fallback)
    """
    from services.scenario_handler import handle as handle_scenario
    from services.parties import get_parties

    # Layer 1: Scenarios
    scenario = handle_scenario(message)
    if scenario:
        return {
            "message": f"### {scenario.title}\n\n" + "\n".join(f"- {s}" for s in scenario.steps),
            "next_action": "Verify information with your local authority.",
            "status": "success"
        }

    # Layer 2: AI
    parties = get_parties(region_id)
    if parties:
        party_context = _build_party_context(parties)
        prompt = _prompt_chat_assist(message, party_context, language)

        try:
            result = call_ai(prompt)
            if result.explanation and result.status == "success":
                return {
                    "message": result.explanation,
                    "next_action": result.action_items[-1] if result.action_items else "Review party manifestos",
                    "status": "success"
                }
        except Exception:
            pass

    # Layer 3: Fallback
    return keyword_fallback(message, parties or [])