import sys

import asyncio
import pytest
from fastapi import HTTPException

import ai_karen_engine.utils.auth as auth_utils
from types import SimpleNamespace

from fastapi.testclient import TestClient  # noqa: E402
from main import create_app, chat, ChatRequest  # noqa: E402

client = TestClient(create_app())

TOKEN = "test-token"

auth_utils.validate_session = lambda t, *_: {
    "sub": "user1",
    "roles": ["user"],
    "tenant_id": "tenantA",
} if t == TOKEN else None


class FakeRequest:
    def __init__(self, headers=None):
        self.headers = headers or {}
        self.client = SimpleNamespace(host="127.0.0.1")


def test_chat_endpoint():
    req = FakeRequest({"authorization": f"Bearer {TOKEN}"})
    data = asyncio.run(chat(ChatRequest(text="hello"), req)).dict()
    assert data["intent"] == "greet"
    assert data["response"] == (
        "Hey there! I'm Kari—your AI co-pilot. What can I help with today?"
    )


def test_deep_reasoning_endpoint():
    req = FakeRequest({"authorization": f"Bearer {TOKEN}"})
    data = asyncio.run(chat(ChatRequest(text="why is the sky blue"), req)).dict()
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
    req = FakeRequest()
    try:
        asyncio.run(chat(ChatRequest(text="hello"), req))
    except HTTPException as exc:
        assert exc.status_code == 401

    req = FakeRequest({"authorization": f"Bearer {TOKEN}"})
    data = asyncio.run(chat(ChatRequest(text="nonsense"), req)).dict()
    assert data["intent"] == "hf_generate"

    req = FakeRequest({"authorization": f"Bearer {TOKEN}"})
    data = asyncio.run(chat(ChatRequest(text="the time"), req)).dict()
    assert data["intent"] == "time_query"


def test_chat_invalid_token():
    req = FakeRequest({"authorization": "Bearer bad"})
    with pytest.raises(HTTPException):
        asyncio.run(chat(ChatRequest(text="hello"), req))


def test_plugin_manifest_not_found():
    resp = client.get("/plugins/bogus")
    assert resp.status_code == 404


def test_select_model_invalid():
    resp = client.post("/models/select", json={"model": "unknown"})
    assert resp.status_code == 404
