from data.firestore_client import get_db


def get_parties(region_id: str) -> list:
    """
    Fetch all parties for a given region_id from Firestore.
    Uses a proper .where() query — same pattern as data_service.get_parties().
    """
    try:
        docs = (
            get_db()
            .collection("parties")
            .where("region_id", "==", region_id)
            .stream()
        )
        result = [doc.to_dict() for doc in docs]

        print(f"DEBUG: Found {len(result)} parties for {region_id}")

        return result

    except Exception as e:
        print("ERROR in get_parties:", str(e))
        return []
