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
from google.api_core import exceptions as google_exceptions
from config import settings

logger = logging.getLogger(__name__)

# Module-level singleton — created once on first call to get_db().
_client: Optional[firestore.Client] = None
# In-memory fallback for local development when Firestore is unavailable.
_use_in_memory = False
_in_memory_store: dict[str, dict] = {}


def get_db() -> firestore.Client:
    """
    Return the shared Firestore client, initialising it on first call.

    Using a module-level singleton avoids creating a new gRPC connection
    on every request, which is expensive.
    """
    global _client
    global _client, _use_in_memory
    if _client is None and not _use_in_memory:
        try:
            _client = firestore.Client(
                project=settings.project_id,
                database=settings.firestore_database,
            )
            logger.info(
                "Firestore client initialised (project=%s, database=%s)",
                settings.project_id,
                settings.firestore_database,
            )
        except Exception as e:
            # If we're running in development, fall back to an in-memory store
            if settings.app_env == 'development':
                _use_in_memory = True
                _in_memory_store.clear()
                logger.warning("Falling back to in-memory Firestore emulation: %s", e)
            else:
                logger.exception("Failed to initialise Firestore client")
                raise

    if _use_in_memory:
        # Return a simple sentinel object when using in-memory mode
        return None

    return _client


def get_document(collection: str, doc_id: str) -> Optional[dict]:
    """
    Fetch a single document by its ID.

    Returns the document as a plain dict, or None if it does not exist.
    Callers should handle the None case explicitly.
    """
    db = get_db()
    if _use_in_memory or db is None:
        coll = _in_memory_store.setdefault(collection, {})
        return coll.get(doc_id)

    doc_ref = db.collection(collection).document(doc_id)
    snapshot = doc_ref.get()
    return snapshot.to_dict() if snapshot.exists else None


def set_document(collection: str, doc_id: str, data: dict) -> None:
    """
    Create or fully overwrite a document.

    Use this for initial writes (e.g. creating a user profile).
    For partial updates, use update_document instead.
    """
    db = get_db()
    if _use_in_memory or db is None:
        coll = _in_memory_store.setdefault(collection, {})
        coll[doc_id] = data.copy()
        return

    get_db().collection(collection).document(doc_id).set(data)


def update_document(collection: str, doc_id: str, data: dict) -> None:
    """
    Merge-update a document — only the provided fields are changed.

    Existing fields not present in `data` are left untouched.
    Use this for progress updates where overwriting the full document
    would risk losing fields written by another path.
    """
    db = get_db()
    if _use_in_memory or db is None:
        coll = _in_memory_store.setdefault(collection, {})
        existing = coll.get(doc_id, {})
        merged = {**existing, **data}
        coll[doc_id] = merged
        return

    get_db().collection(collection).document(doc_id).set(data, merge=True)

def get_collection(collection_name: str):
    db = get_db()
    if _use_in_memory or db is None:
        coll = _in_memory_store.setdefault(collection_name, {})
        return list(coll.values())

    return [doc.to_dict() for doc in db.collection(collection_name).stream()]
