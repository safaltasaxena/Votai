"""
models/progress.py — User journey progress model.

Tracks where a user is in the 5-step election journey.
Stored in the Firestore `progress` collection, keyed by user_id.

Kept separate from UserProfile because:
- Progress is written frequently (on every step advance).
- Profile is written once and rarely read again after onboarding.
- Separating them avoids unnecessary full-document overwrites.
"""

from typing import Literal
from pydantic import BaseModel, Field

# Valid states for a single step in step_status.
StepState = Literal["pending", "current", "completed"]


class UserProgress(BaseModel):
    """
    Mutable journey state for a single user.
    Updated by user_service on every step transition.
    """

    user_id: str = Field(
        ...,
        description="Matches the user_id in the `users` collection."
    )
    current_step: int = Field(
        default=1,
        ge=1,
        le=5,
        description="The step the user is actively working on. Controlled only by flow_engine."
    )
    completed_steps: list[int] = Field(
        default_factory=list,
        description="Ordered list of step numbers the user has finished."
    )
    step_status: dict[str, StepState] = Field(
        default_factory=dict,
        description=(
            "Map of step number (as string key) to its state. "
            "Populated by user_service on each advance. "
            "Keys are '1' through '5'. "
            "Example: {'1': 'completed', '2': 'current', '3': 'pending'}"
        )
    )
    onboarding_done: bool = Field(
        default=False,
        description="True once the user has completed the profile form and journey has started."
    )
