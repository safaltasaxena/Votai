"""
data/firestore_client.py — Firestore connection and generic CRUD helpers.

Responsibilities (this file only):
  - Initialise and hold a single Firestore client (singleton).
  - Expose three generic helper methods: get, set, update.

What does NOT belong here:
  - Business logic (that lives in services/).
  - Collection name constants (those belong to each service).
  - Query or filter logic beyond a direct document lookup.
"""

import logging
from typing import Optional

from google.cloud import firestore
from backend.config import settings

logger = logging.getLogger(__name__)

# Module-level singleton — created once on first call to get_db().
_client: Optional[firestore.Client] = None


def get_db() -> firestore.Client:
    """
    Return the shared Firestore client, initialising it on first call.

    Using a module-level singleton avoids creating a new gRPC connection
    on every request, which is expensive.
    """
    global _client
    if _client is None:
        _client = firestore.Client(
            project=settings.project_id,
            database=settings.firestore_database,
        )
        logger.info(
            "Firestore client initialised (project=%s, database=%s)",
            settings.project_id,
            settings.firestore_database,
        )
    return _client


def get_document(collection: str, doc_id: str) -> Optional[dict]:
    """
    Fetch a single document by its ID.

    Returns the document as a plain dict, or None if it does not exist.
    Callers should handle the None case explicitly.
    """
    doc_ref = get_db().collection(collection).document(doc_id)
    snapshot = doc_ref.get()
    return snapshot.to_dict() if snapshot.exists else None


def set_document(collection: str, doc_id: str, data: dict) -> None:
    """
    Create or fully overwrite a document.

    Use this for initial writes (e.g. creating a user profile).
    For partial updates, use update_document instead.
    """
    get_db().collection(collection).document(doc_id).set(data)


def update_document(collection: str, doc_id: str, data: dict) -> None:
    """
    Merge-update a document — only the provided fields are changed.

    Existing fields not present in `data` are left untouched.
    Use this for progress updates where overwriting the full document
    would risk losing fields written by another path.
    """
    get_db().collection(collection).document(doc_id).set(data, merge=True)

def get_collection(collection_name: str):
    db = get_db()
    return [doc.to_dict() for doc in db.collection(collection_name).stream()]
