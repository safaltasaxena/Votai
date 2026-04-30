from backend.data.firestore_client import get_collection


def get_parties(region_id: str):
    """
    Fetch all parties for a given region_id from Firestore.
    """

    try:
        docs = get_collection("parties")

        # Filter by region_id
        result = [
            doc for doc in docs
            if doc.get("region_id") == region_id
        ]

        print(f"DEBUG: Found {len(result)} parties for {region_id}")

        return result

    except Exception as e:
        print("ERROR in get_parties:", str(e))
        return []
