"""
routers/parties.py — Party data endpoints.

Routes:
  GET /parties/{region_id}             → all parties for a region
  GET /parties/{region_id}/{party_id}  → single party details

NEUTRALITY RULE (enforced here):
  - Data is returned as-is from Firestore — no sorting, no ranking.
  - A disclaimer is appended to every response.
  - No AI, no scoring, no comparison logic.

Delegates all data fetching to data_service.
"""

import logging

from fastapi import APIRouter, HTTPException

from backend.services.data_service import get_parties, get_party

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/parties", tags=["Parties"])

# Mandatory disclaimer — appended to every party response per gemini.md.
_PARTY_DISCLAIMER = (
    "This information is provided for awareness only and does not "
    "recommend or endorse any candidate or party."
)


@router.get("/{region_id}")
async def list_parties(region_id: str):
    """
    Return all parties for a region.

    Order of results is determined by Firestore — no ranking applied.
    The disclaimer is always included in the response.
    """
    parties = get_parties(region_id)

    if not parties:
        raise HTTPException(
            status_code=404,
            detail=f"No party data found for region '{region_id}'. "
                   f"Data may not have been seeded yet.",
        )

    logger.info("Parties fetched (region_id=%s, count=%d)", region_id, len(parties))

    return {
        "success": True,
        "region_id": region_id,
        "count": len(parties),
        "disclaimer": _PARTY_DISCLAIMER,
        "parties": parties,
    }


@router.get("/{region_id}/{party_id}")
async def get_party_detail(region_id: str, party_id: str):
    """
    Return a single party's details.

    Validates that the party belongs to the requested region.
    Returns 404 if the party does not exist or belongs to a different region.
    The disclaimer is always included in the response.
    """
    party = get_party(region_id, party_id)

    if party is None:
        raise HTTPException(
            status_code=404,
            detail=f"Party '{party_id}' not found in region '{region_id}'.",
        )

    logger.info("Party fetched (region_id=%s, party_id=%s)", region_id, party_id)

    return {
        "success": True,
        "disclaimer": _PARTY_DISCLAIMER,
        "party": party,
    }
