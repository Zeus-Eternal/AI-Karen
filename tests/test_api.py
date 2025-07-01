import sys

import fastapi_stub
import pydantic_stub

sys.modules["fastapi"] = fastapi_stub
sys.modules["pydantic"] = pydantic_stub

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

client = TestClient(app)


def test_chat_endpoint():
    resp = client.post("/chat", json={"text": "hello", "role": "user"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "greet"
    assert data["response"] == (
        "Hey there! I'm Kari—your AI co-pilot. What can I help with today?"
    )


def test_deep_reasoning_endpoint():
    resp = client.post("/chat", json={"text": "why is the sky blue"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "deep_reasoning"
    assert "entropy" in data["response"]


def test_ping():
    resp = client.get("/ping")
    assert resp.status_code == 200

    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "plugins" in data

    resp = client.get("/ready")
    assert resp.status_code == 200


def test_store_and_search():
    resp = client.post(
        "/store", json={"text": "memory test", "ttl_seconds": 1, "tag": "keep"}
    )
    assert resp.status_code == 200
    resp = client.post(
        "/search",
        json={"text": "memory", "metadata_filter": {"tag": "keep"}},
    )
    assert resp.status_code == 200
    results = resp.json()
    assert results[0]["payload"]["text"] == "memory test"


def test_plugin_management():
    resp = client.get("/plugins")
    assert resp.status_code == 200
    assert "greet" in resp.json()
    resp = client.get("/plugins/greet")
    assert resp.status_code == 200
    manifest = resp.json()
    assert manifest["intent"] == "greet"
    resp = client.post("/plugins/reload")
    assert resp.status_code == 200


def test_chat_errors():
    resp = client.post("/chat", json={"text": "hello", "role": "guest"})
    assert resp.status_code == 403

    resp = client.post("/chat", json={"text": "nonsense"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "hf_generate"

    resp = client.post("/chat", json={"text": "the time"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "time_query"


def test_plugin_manifest_not_found():
    resp = client.get("/plugins/bogus")
    assert resp.status_code == 404


def test_select_model_invalid():
    resp = client.post("/models/select", json={"model": "unknown"})
    assert resp.status_code == 404
