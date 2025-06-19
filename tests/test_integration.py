from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_chat_endpoint():
    resp = client.post("/chat", json={"text": "hello", "role": "user"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "greet"
    assert data["response"] == "Hello World from plugin!"


def test_deep_reasoning_endpoint():
    resp = client.post("/chat", json={"text": "why is the sky blue", "role": "user"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "deep_reasoning"
    assert "entropy" in data["response"]


def test_ping():
    resp = client.get("/ping")
    assert resp.status_code == 200


def test_store_and_search():
    resp = client.post("/store", json={"text": "memory test"})
    assert resp.status_code == 200
    resp = client.post("/search", json={"text": "memory"})
    assert resp.status_code == 200
    results = resp.json()
    assert results[0]["payload"]["text"] == "memory test"
