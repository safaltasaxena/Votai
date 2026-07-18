from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_onboard():
    payload = {
        "user_id": "test_user_123",
        "age": 25,
        "country": "India",
        "state": "Maharashtra",
        "language": "en",
        "first_time_voter": True
    }
    res = client.post("/journey/onboard", json=payload)
    assert res.status_code == 200
    assert "current_step" in res.json()

def test_parties():
    res = client.get("/parties/IN-MH")
    assert res.status_code == 200
    assert "parties" in res.json()

def test_ai_fallback():
    # Note: This might hit the real AI service or a mock depending on setup.
    # In a real test environment, we'd mock the AI service.
    res = client.post("/ai/chat", json={
        "message": "healthcare",
        "region_id": "IN-MH"
    })
    assert res.status_code == 200
    data = res.json()
    assert "message" in data
    assert "status" in data
