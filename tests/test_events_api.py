import time
from fastapi.testclient import TestClient
from main import app
from ai_karen_engine.event_bus import get_event_bus

client = TestClient(app)


def test_events_endpoint_auth():
    # login
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    assert resp.status_code == 200
    token = resp.json()["token"]

    bus = get_event_bus()
    bus.publish("caps", "ping", {"ts": time.time()}, roles=["admin"], tenant_id="acme")

    resp = client.get("/api/events/", headers={"Authorization": f"Bearer {token}", "user-agent": "test", "host": "test"})
    assert resp.status_code == 200
    data = resp.json()
    assert data and data[0]["capsule"] == "caps"


def test_events_endpoint_unauth():
    resp = client.get("/api/events/")
    assert resp.status_code == 401
