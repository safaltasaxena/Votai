"""
routers/journey.py — User onboarding and step navigation endpoints.

Routes:
  POST /journey/onboard          → create user, initialise progress, return Step 1
  GET  /journey/{user_id}/step   → return current step (+ scenario check slot)
  POST /journey/{user_id}/advance → mark step complete, move to next

ARCHITECTURE RULES ENFORCED HERE:
  1. All step logic goes through flow_engine — never computed in this file.
  2. scenario_handler is checked before any future AI call.
     If it returns a resolution, the response is built and returned immediately.
  3. No Firestore access directly — only through user_service.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.models.user import UserProfile
from backend.models.response import VotaiResponse
from backend.services import flow_engine, user_service, scenario_handler
from backend.services.flow_engine import get_step, get_next_step, calculate_readiness

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/journey", tags=["Journey"])


# ── Request bodies ─────────────────────────────────────────────────────────────

class OnboardRequest(BaseModel):
    """Data collected from the onboarding form."""
    user_id: str
    age: int
    country: str
    state: str
    language: str = "en"
    first_time_voter: bool = True


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/onboard", response_model=VotaiResponse)
async def onboard_user(req: OnboardRequest):
    """
    Create a user profile and initialise progress at Step 1.

    Idempotent: calling this again for the same user_id overwrites
    the profile but resets progress — intended for re-onboarding.
    """
    profile = UserProfile(**req.model_dump())
    user_service.create_user(profile)

    # Initialise progress — get_progress creates and saves the default if absent.
    progress = user_service.get_progress(req.user_id)

    current_step = get_step(progress.current_step)
    next_step = get_next_step(progress.current_step)

    logger.info("User onboarded (user_id=%s, step=%d)", req.user_id, progress.current_step)

    return VotaiResponse(
        current_step=current_step,
        next_step=next_step,
        action_items=["Complete Step 1 to begin your journey."],
    )


@router.get("/{user_id}/step", response_model=VotaiResponse)
async def get_current_step(
    user_id: str,
    message: Optional[str] = Query(default=None, description="Optional user question about the current step."),
):
    """
    Return the user's current step and relevant context.

    If a message is provided:
      1. Check scenario_handler first.
      2. If a scenario is matched → return its resolution immediately.
      3. Otherwise → return step info (Phase 2 will add AI explanation here).

    This structure ensures scenario-first handling is in place
    before AI is integrated in Phase 2.
    """
    progress = user_service.get_progress(user_id)
    current_step = get_step(progress.current_step)
    next_step = get_next_step(progress.current_step)

    # ── Scenario-first check (runs before any future AI call) ─────────────────
    if message:
        resolution = scenario_handler.handle(message)
        if resolution:
            logger.info(
                "Scenario matched (user_id=%s, scenario=%s)",
                user_id, resolution.scenario_key,
            )
            return VotaiResponse(
                current_step=current_step,
                next_step=next_step,
                explanation=resolution.title,
                action_items=resolution.steps + [resolution.fallback_note],
            )
    # ── Phase 2: AI explanation call will be inserted here ────────────────────

    return VotaiResponse(
        current_step=current_step,
        next_step=next_step,
    )


@router.post("/{user_id}/advance", response_model=VotaiResponse)
async def advance_step(user_id: str):
    """
    Mark the current step complete and move the user to the next one.

    Step advancement is handled entirely by flow_engine via user_service.
    This route does no step computation of its own.
    """
    updated_progress = user_service.advance_step(user_id)
    readiness = calculate_readiness(updated_progress.completed_steps)

    current_step = get_step(updated_progress.current_step)
    next_step = get_next_step(updated_progress.current_step)

    logger.info(
        "Step advanced (user_id=%s, current=%d, readiness=%d%%)",
        user_id, updated_progress.current_step, readiness,
    )

    return VotaiResponse(
        current_step=current_step,
        next_step=next_step,
        action_items=[f"You are {readiness}% ready. Keep going!"],
    )
