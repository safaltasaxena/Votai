import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.models.user import UserProfile
from backend.models.response import VotaiResponse
from backend.services import user_service, scenario_handler, ai_service
from backend.services.flow_engine import get_step, get_next_step, calculate_readiness

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/journey", tags=["Journey"])


# ── Request model ─────────────────────────────────────────────────────────────

class OnboardRequest(BaseModel):
    user_id: str
    age: int
    country: str
    state: str
    language: str = "en"
    first_time_voter: bool = True


# ── Onboarding ────────────────────────────────────────────────────────────────

@router.post("/onboard", response_model=VotaiResponse)
async def onboard_user(req: OnboardRequest):
    try:
        profile = UserProfile(**req.model_dump())
        user_service.create_user(profile)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    progress = user_service.get_progress(req.user_id)

    current_step = get_step(progress.current_step)
    next_step = get_next_step(progress.current_step)

    return VotaiResponse(
        current_step=current_step,
        next_step=next_step,
        explanation=current_step.description,
        action_items=[],
        next_action=current_step.next_action
    )


# ── Get Current Step ──────────────────────────────────────────────────────────

@router.get("/{user_id}/step", response_model=VotaiResponse)
async def get_current_step(
    user_id: str,
    region_id: Optional[str] = Query(default="IN-MH", alias="region"),
    message: Optional[str] = Query(default=None),
):
    progress = user_service.get_progress(user_id)

    current_step = get_step(progress.current_step)
    next_step = get_next_step(progress.current_step)

    # ✅ FIX 1: Proper readiness calculation
    readiness = calculate_readiness(progress.completed_steps)
    current_step.percentage = readiness

    # ✅ FIX 2: Correct completion condition
    if progress.current_step == 5 and len(progress.completed_steps) == 5:
        return VotaiResponse(
            current_step=current_step,
            completed=True,
            message="🎉 You are ready to vote",
            action_items=["Visit polling booth on election day"]
        )

    # ── Scenario + AI handling ───────────────────────────────────────────────
    if message:
        resolution = scenario_handler.handle(message)
        if resolution:
            return VotaiResponse(
                current_step=current_step,
                next_step=next_step,
                explanation=resolution.title,
                action_items=resolution.steps + [resolution.fallback_note],
            )

        # Fetch user context
        user_profile = user_service.get_user(user_id)
        language = user_profile.language if user_profile else "en"
        is_first_time = user_profile.first_time_voter if user_profile else True

        # ✅ FIX 3: Inject first-time voter context into AI
        enhanced_message = message + ("User type: First-time voter → explain in beginner-friendly way, include step-by-step clarity\n\nUser type: Returning voter → skip basics, focus on verification and updates" if is_first_time else "")

        result = ai_service.explain_step(
            step_name=current_step.step_name,
            step_description=current_step.description,
            user_message=enhanced_message,
            region=region_id,
            language=language,
        )

        return VotaiResponse(
            current_step=current_step,
            next_step=next_step,
            explanation=result.explanation,
            action_items=result.action_items,
            disclaimer=result.disclaimer,
        )

    # ✅ FIX 4: NEVER return empty UI
    return VotaiResponse(
        current_step=current_step,
        next_step=next_step,
        explanation=current_step.description,
        action_items=[],
        next_action=current_step.next_action
    )


# ── Advance Step ──────────────────────────────────────────────────────────────

@router.post("/{user_id}/advance", response_model=VotaiResponse)
async def advance_step(user_id: str):
    updated_progress = user_service.advance_step(user_id)

    current_step = get_step(updated_progress.current_step)
    next_step = get_next_step(updated_progress.current_step)

    # ✅ FIX 5: readiness properly assigned
    readiness = calculate_readiness(updated_progress.completed_steps)
    current_step.percentage = readiness

    # ✅ FIX 6: Correct completion logic
    if updated_progress.current_step == 5 and len(updated_progress.completed_steps) == 5:
        return VotaiResponse(
            current_step=current_step,
            completed=True,
            message="🎉 You are ready to vote",
            action_items=["Visit polling booth on election day"]
        )

    return VotaiResponse(
        current_step=current_step,
        next_step=next_step,
        explanation=current_step.description,
        action_items=[],
        next_action=current_step.next_action
    )