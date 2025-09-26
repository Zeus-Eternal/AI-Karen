"""Tests for the chat runtime API routes."""

import json
import os
from types import SimpleNamespace
from typing import Any, AsyncIterator, Dict

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("KARI_DUCKDB_PASSWORD", "test-password")
os.environ.setdefault("KARI_JOB_SIGNING_KEY", "test-signing-key-0123456789abcdef")
os.environ.setdefault("KARI_DUCKDB_SALT", "test-salt")

from ai_karen_engine.api_routes import chat_runtime


class _FakeOrchestrator:
    """Minimal orchestrator used for route testing."""

    async def process_message(self, chat_request: chat_runtime.ChatRequest):  # type: ignore[override]
        if chat_request.stream:
            async def _stream() -> AsyncIterator[SimpleNamespace]:
                yield SimpleNamespace(type="metadata", metadata={"phase": "start"}, content="")
                yield SimpleNamespace(type="content", content="Hello world", metadata={})
                yield SimpleNamespace(
                    type="complete",
                    content="",
                    metadata={"total_latency": 42.0, "first_token_latency": 10.0},
                )

            return _stream()

        return SimpleNamespace(
            response="Hello world",
            correlation_id="corr-123",
            processing_time=12.5,
            metadata={"model": "test-model"},
        )


class _FakeDecision:
    def __init__(self) -> None:
        self.provider = "test-provider"
        self.model = "test-model"
        self.reasoning = "deterministic routing"
        self.confidence = 0.9
        self.fallback_chain = ["fallback"]


class _FakeRegistry:
    async def get_provider_with_routing(self, **_: Any) -> Dict[str, Any]:  # type: ignore[override]
        return {"decision": _FakeDecision()}


class _NoDecisionRegistry:
    async def get_provider_with_routing(self, **_: Any) -> Dict[str, Any]:  # type: ignore[override]
        return {"decision": None}


@pytest.fixture()
def test_app(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create a FastAPI app with overridden dependencies for testing."""

    app = FastAPI()
    app.include_router(chat_runtime.router)

    app.dependency_overrides[chat_runtime.get_chat_orchestrator] = lambda: _FakeOrchestrator()
    app.dependency_overrides[chat_runtime.get_current_user_context] = lambda: {"user_id": "tester"}
    app.dependency_overrides[chat_runtime.get_request_metadata] = lambda: {
        "ip_address": "127.0.0.1",
        "user_agent": "pytest",
        "platform": "web",
        "client_id": "client-123",
        "correlation_id": "corr-123",
    }

    monkeypatch.setattr(chat_runtime, "get_registry", lambda: _FakeRegistry())

    return TestClient(app)


def test_chat_runtime_returns_response(test_app: TestClient) -> None:
    """The non-streaming chat runtime route should return a JSON payload."""

    response = test_app.post("/chat/runtime", json={"message": "Hello"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["content"] == "Hello world"
    assert payload["metadata"]["kire_metadata"]["provider"] == "test-provider"


def test_chat_runtime_stream_emits_tokens(test_app: TestClient) -> None:
    """The streaming chat runtime route should emit SSE token events."""

    with test_app.stream("POST", "/chat/runtime/stream", json={"message": "Stream please"}) as response:
        # Collect the streamed lines so json.dumps is exercised
        lines = list(response.iter_lines())

    assert response.status_code == 200
    # Ensure at least one token and completion event were emitted
    assert any("\"type\": \"token\"" in line for line in lines)
    assert any("\"type\": \"complete\"" in line for line in lines)


def test_chat_runtime_stream_handles_missing_kire(test_app: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Streaming should still work if the routing engine returns no decision."""

    monkeypatch.setattr(chat_runtime, "get_registry", lambda: _NoDecisionRegistry())

    with test_app.stream("POST", "/chat/runtime/stream", json={"message": "Stream please"}) as response:
        lines = list(response.iter_lines())

    assert response.status_code == 200
    metadata_lines = [line for line in lines if '"type": "metadata"' in line]
    assert metadata_lines, "Expected at least one metadata event"
    payload = json.loads(metadata_lines[0].split("data: ", 1)[1])
    assert "kire" not in payload["data"]
