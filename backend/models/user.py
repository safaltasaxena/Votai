"""
models/user.py — User profile model.

Represents the data collected during onboarding.
Stored in the Firestore `users` collection, keyed by user_id.

No business logic here — this is a pure data shape.
"""

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """
    Immutable snapshot of a user's onboarding answers.
    Written once at journey start; not updated after creation.
    """

    user_id: str = Field(
        ...,
        description="Session-generated unique identifier. Used as the Firestore document ID."
    )
    age: int = Field(
        ...,
        ge=1,
        le=150,
        description="User's age. Used for eligibility context, not enforcement."
    )
    country: str = Field(
        ...,
        description="User's country (e.g. 'India'). Top-level region scope."
    )
    state: str = Field(
        ...,
        description="User's state or sub-region (e.g. 'Maharashtra'). Maps to an elections document."
    )
    language: str = Field(
        default="en",
        description="BCP-47 language code for AI response language (e.g. 'en', 'hi')."
    )
    first_time_voter: bool = Field(
        default=True,
        description="Personalisation signal. Does not gate any feature — only adjusts explanation depth."
    )
