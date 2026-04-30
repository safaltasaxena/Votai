"""
services/user_service.py — All user profile and progress operations.

This is the only service that reads or writes the `users` and
`progress` Firestore collections. No other service or router
should touch these collections directly.

Depends on:
  - data/firestore_client.py (generic CRUD only)
  - services/flow_engine.py (step transitions and step_status map)
  - models/user.py, models/progress.py
"""

import logging
from datetime import datetime, timezone

from backend.data.firestore_client import get_document, set_document, update_document
from backend.models.user import UserProfile
from backend.models.progress import UserProgress
from backend.services.flow_engine import (
    FIRST_STEP,
    LAST_STEP,
    build_step_status,
)

logger = logging.getLogger(__name__)

# Collection names are owned by this service — not scattered across routers.
_USERS_COLLECTION = "users"
_PROGRESS_COLLECTION = "progress"


# ── User profile ───────────────────────────────────────────────────────────────

def create_user(profile: UserProfile) -> None:
    """
    Persist a new user profile to Firestore.

    Called once at onboarding. The document ID equals the user_id,
    making profile lookups an O(1) direct fetch.
    """
    data = profile.model_dump()
    data["created_at"] = _utc_now()
    set_document(_USERS_COLLECTION, profile.user_id, data)
    logger.info("User profile created (user_id=%s)", profile.user_id)


def get_user(user_id: str) -> UserProfile | None:
    """
    Fetch a user profile by ID.

    Returns None if the user has not completed onboarding yet.
    Callers must handle the None case explicitly.
    """
    raw = get_document(_USERS_COLLECTION, user_id)
    if raw is None:
        return None
    return UserProfile(**raw)


# ── Progress ───────────────────────────────────────────────────────────────────

def get_progress(user_id: str) -> UserProgress:
    """
    Fetch user progress, defaulting to a fresh Step 1 state for new users.

    If no progress document exists, a default is created and saved to
    Firestore before returning. This ensures the document is present for
    all subsequent reads — avoiding repeated default-construction on every
    request before the user has advanced their first step.

    Always returns a valid UserProgress — never None.
    """
    raw = get_document(_PROGRESS_COLLECTION, user_id)
    if raw:
        return UserProgress(**raw)

    # First visit: build a default state, persist it, then return it.
    default_progress = UserProgress(
        user_id=user_id,
        current_step=FIRST_STEP,
        completed_steps=[],
        step_status=build_step_status(FIRST_STEP, []),
    )
    save_progress(default_progress)
    logger.info("Default progress created (user_id=%s)", user_id)
    return default_progress


def save_progress(progress: UserProgress) -> None:
    """
    Persist (merge-update) user progress to Firestore.

    Uses merge=True so only the provided fields are overwritten —
    adjacent fields written by other code paths are preserved.
    """
    data = progress.model_dump()
    data["last_updated"] = _utc_now()
    update_document(_PROGRESS_COLLECTION, progress.user_id, data)


def advance_step(user_id: str) -> UserProgress:
    """
    Mark the current step complete and move to the next one.

    Delegates all step-number logic to flow_engine.
    Returns the updated UserProgress so the router can embed it
    in the response without a second Firestore read.
    """
    progress = get_progress(user_id)
    current = progress.current_step

    # Record completion (deduplicated by converting to set in readiness calc).
    if current not in progress.completed_steps:
        progress.completed_steps.append(current)

    # Advance only if not already on the final step.
    if current < LAST_STEP:
        progress.current_step = current + 1

    # Rebuild the step_status map to reflect the new state.
    progress.step_status = build_step_status(
        progress.current_step, progress.completed_steps
    )

    save_progress(progress)
    logger.info(
        "Step advanced (user_id=%s, from=%d, to=%d)",
        user_id, current, progress.current_step,
    )
    return progress


# ── Internal helpers ───────────────────────────────────────────────────────────

def _utc_now() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()
