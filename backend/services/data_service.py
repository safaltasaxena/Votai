"""
services/data_service.py — Election and party data retrieval.

Responsibilities (this service only):
  - Fetch election documents from Firestore.
  - Fetch party documents from Firestore.
  - Format raw Firestore data into clean dicts for routers.

What does NOT belong here:
  - Business logic (step decisions, eligibility checks).
  - AI prompt construction (that belongs to ai_service, Phase 2).
  - User state reads/writes (that belongs to user_service).

Firestore collections accessed: `elections`, `parties`.
"""

import logging
from typing import Optional

from backend.data.firestore_client import get_document, get_db

logger = logging.getLogger(__name__)

# Collection names owned by this service.
_ELECTIONS_COLLECTION = "elections"
_PARTIES_COLLECTION = "parties"


def get_election(region_id: str) -> Optional[dict]:
    """
    Fetch the election document for a given region.

    The document ID is the region code (e.g. "IN-MH", "IN-DL").
    Returns None if no election data has been seeded for this region.
    Callers must handle the None case and respond with a fallback.
    """
    data = get_document(_ELECTIONS_COLLECTION, region_id)

    if data is None:
        logger.warning("No election data found (region_id=%s)", region_id)

    return data


def get_parties(region_id: str) -> list[dict]:
    """
    Fetch all party documents for a given region.

    Queries the `parties` collection where region_id matches.
    Returns an empty list if no parties are seeded — never raises.

    Results are returned as-is from Firestore.
    No ranking, sorting, or filtering is applied here.
    """
    try:
        docs = (
            get_db()
            .collection(_PARTIES_COLLECTION)
            .where("region_id", "==", region_id)
            .stream()
        )
        parties = [doc.to_dict() for doc in docs]

        if not parties:
            logger.warning("No parties found (region_id=%s)", region_id)

        return parties

    except Exception as exc:
        # Log and return empty list — a missing party list
        # should not break the user's journey.
        logger.error("Failed to fetch parties (region_id=%s): %s", region_id, exc)
        return []


def get_party(region_id: str, party_id: str) -> Optional[dict]:
    """
    Fetch a single party document by its document ID.

    Returns None if the party does not exist.
    """
    data = get_document(_PARTIES_COLLECTION, party_id)

    # Confirm the party belongs to the requested region before returning.
    if data and data.get("region_id") != region_id:
        logger.warning(
            "Party found but region mismatch (party_id=%s, expected=%s, got=%s)",
            party_id, region_id, data.get("region_id"),
        )
        return None

    return data
