"""
routers/elections.py — Election data endpoints.

Routes:
  GET /elections/{region_id}          → full election document for a region
  GET /elections/{region_id}/timeline → deadlines and process steps only

Delegates all data fetching to data_service.
No step logic. No user state. No AI.
"""

import logging

from fastapi import APIRouter, HTTPException

from services.data_service import get_election

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/elections", tags=["Elections"])


@router.get("/{region_id}")
async def get_election_data(region_id: str):
    """
    Return the full election document for a region (e.g. 'IN-MH').

    Returns 404 if no election data has been seeded for this region.
    The frontend should use this to show region-specific context.
    """
    data = get_election(region_id)

    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No election data found for region '{region_id}'. "
                   f"Please verify the region code or contact support.",
        )

    return {"success": True, "region_id": region_id, "data": data}


@router.get("/{region_id}/timeline")
async def get_election_timeline(region_id: str):
    """
    Return only the deadline and process-step data for a region.

    A lightweight subset of the full election document —
    used by the frontend to render the timeline view without
    loading the full document (including polling_info, notes, etc.).
    """
    data = get_election(region_id)

    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No election data found for region '{region_id}'.",
        )

    # Extract only the fields needed for the timeline view.
    timeline = {
    "region_id": region_id,
    "state": data.get("state"),
    "election_date": data.get("election_date") or "Not available",
    "registration_deadline": data.get("registration_deadline") or "Not available",
    "verification_deadline": data.get("verification_deadline") or "Not available",
    "process_steps": data.get("process_steps", []),
    "official_portal": data.get("official_portal"),
    }

    return {"success": True, "timeline": timeline}
