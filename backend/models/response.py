"""
models/response.py — Shared API response schema.

Every endpoint returns a VotaiResponse.
This ensures the frontend always receives a consistent,
predictable shape — regardless of which router produced it.

No business logic here. This is purely a contract definition.
"""

from typing import Optional
from pydantic import BaseModel, Field


class StepInfo(BaseModel):
    """
    Metadata for a single journey step.
    Produced by flow_engine and embedded in every response.
    """

    step_number: int = Field(..., ge=1, le=5)
    step_name: str = Field(..., description="Human-readable step label.")
    description: str = Field(..., description="What this step is about.")


class VotaiResponse(BaseModel):
    """
    Standard response envelope returned by all Votai endpoints.

    Fields are optional where the value is not yet available
    (e.g. explanation is empty before AI integration).
    """

    success: bool = Field(
        default=True,
        description="False only when the request itself failed (not when data is missing)."
    )

    # ── Step context ───────────────────────────────────────────────────────────
    current_step: StepInfo
    next_step: Optional[StepInfo] = Field(
        default=None,
        description="None when the user is on the final step."
    )

    # ── Content (populated once AI is integrated in Phase 2) ──────────────────
    explanation: Optional[str] = Field(
        default=None,
        description="Plain-language explanation of the current step or answer."
    )
    action_items: list[str] = Field(
        default_factory=list,
        description="Bullet-point next actions for the user."
    )

    # ── Metadata ───────────────────────────────────────────────────────────────
    disclaimer: Optional[str] = Field(
        default=None,
        description="Injected by safety_guard for party/candidate topics."
    )
    error: Optional[str] = Field(
        default=None,
        description="Human-readable error message when success is False."
    )
