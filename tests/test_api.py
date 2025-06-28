import sys

import fastapi_stub as fastapi
import pydantic_stub as pydantic
from fastapi_stub.testclient import TestClient

sys.modules.setdefault("fastapi", fastapi)
sys.modules.setdefault("pydantic", pydantic)

from main import app

client = TestClient(app)


def test_chat_endpoint():
    resp = client.post("/chat", json={"text": "hello", "role": "user"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "greet"
    assert data["response"] == "Hello World from plugin!"


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
