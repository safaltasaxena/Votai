"""
services/flow_engine.py — Single source of truth for all step logic.

RULE: No router, service, or model may compute step numbers, step names,
or step transitions independently. Everything goes through this module.

Responsibilities:
  - Define and own the 5-step journey registry.
  - Resolve current step metadata.
  - Determine the next step (or None at journey end).
  - Calculate readiness percentage.
  - Build the step_status map written to Firestore progress.

No Firestore access. No AI calls. Fully deterministic.
"""

from backend.models.response import StepInfo
from backend.models.progress import StepState


# ── Journey registry ──────────────────────────────────────────────────────────
# This is the canonical definition of every step in the system.
# To add, rename, or reorder a step: change it here only.

JOURNEY_STEPS: dict[int, StepInfo] = {
    1: StepInfo(
        step_number=1,
        step_name="Eligibility Check",
        description="Confirm you meet the legal requirements to vote in your region.",
        percentage=20,
        next_action="Complete your eligibility checklist."
    ),
    2: StepInfo(
        step_number=2,
        step_name="Voter Registration",
        description="Register as a voter — documents needed, deadlines, and how to apply.",
        percentage=40,
        next_action="Submit your registration form."
    ),
    3: StepInfo(
        step_number=3,
        step_name="List Verification",
        description="Confirm your name appears correctly in the voter list and collect your Voter ID.",
        percentage=60,
        next_action="Check the electoral roll for your name."
    ),
    4: StepInfo(
        step_number=4,
        step_name="Candidate Understanding",
        description="Learn about the election, parties, and candidates in a neutral, factual way.",
        percentage=80,
        next_action="Review party manifestos and past work."
    ),
    5: StepInfo(
        step_number=5,
        step_name="Voting Day Simulation",
        description="Walk through what to expect on election day — from arrival to casting your vote.",
        percentage=100,
        next_action="Prepare for election day.",
        simulation_steps=[
            {"title": "Arrival", "desc": "Go to polling booth"},
            {"title": "Verification", "desc": "Show ID"},
            {"title": "Voting", "desc": "Use EVM"},
            {"title": "Exit", "desc": "Ink mark applied"}
        ]
    ),
}

TOTAL_STEPS: int = len(JOURNEY_STEPS)
FIRST_STEP: int = 1
LAST_STEP: int = TOTAL_STEPS


def get_step(step_number: int) -> StepInfo:
    """
    Return metadata for a given step number.

    Raises ValueError for any step outside the valid range.
    All callers should use this instead of indexing JOURNEY_STEPS directly,
    so validation is centralised here.
    """
    if step_number not in JOURNEY_STEPS:
        raise ValueError(
            f"Invalid step number: {step_number}. Must be between {FIRST_STEP} and {LAST_STEP}."
        )
    return JOURNEY_STEPS[step_number]


def get_next_step(current_step: int) -> StepInfo | None:
    """
    Return the next step's metadata, or None if the user is on the final step.

    Callers should check for None to know when the journey is complete.
    """
    next_number = current_step + 1
    return JOURNEY_STEPS.get(next_number)


def calculate_readiness(completed_steps: list[int]) -> int:
    """
    Return journey readiness as a whole-number percentage (0–100).

    Deduplicates the input list so repeated entries don't inflate the score.
    """
    unique_completed = len(set(completed_steps))
    return round((unique_completed / TOTAL_STEPS) * 100)


def build_step_status(current_step: int, completed_steps: list[int]) -> dict[str, StepState]:
    """
    Build the step_status map stored in Firestore progress documents.

    Each key is a stringified step number ("1"–"5").
    Each value is one of: "completed", "current", "pending".

    This map lets the frontend render the progress bar without
    computing any step logic client-side.
    """
    completed_set = set(completed_steps)
    status: dict[str, StepState] = {}

    for step_num in range(FIRST_STEP, LAST_STEP + 1):
        if step_num in completed_set:
            status[str(step_num)] = "completed"
        elif step_num == current_step:
            status[str(step_num)] = "current"
        else:
            status[str(step_num)] = "pending"

    return status


def is_final_step(step: int) -> bool:
    """
    Return True if the given step is the last step in the journey.

    Use this instead of comparing directly against LAST_STEP or the
    integer 5 in routers and services — keeps the boundary check in
    one place so changing the journey length requires no other edits.
    """
    return step == LAST_STEP
