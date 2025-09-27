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

    def __init__(self) -> None:
        self.calls: list[chat_runtime.ChatRequest] = []

    async def process_message(self, chat_request: chat_runtime.ChatRequest):  # type: ignore[override]
        self.calls.append(chat_request)
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


class _FakeResponseCoreOrchestrator:
    """Stubbed response core orchestrator used for testing the prompt flow."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, Dict[str, Any]]] = []

    def respond(self, message: str, ui_caps: Dict[str, Any] | None = None) -> Dict[str, Any]:  # type: ignore[override]
        ui_caps = ui_caps or {}
        self.calls.append((message, ui_caps))
        return {
            "content": "Response core says hello",
            "intent": "greeting",
            "persona": "default",
            "mood": "cheerful",
            "metadata": {"route": "response-core"},
        }


@pytest.fixture()
def fake_orchestrator() -> _FakeOrchestrator:
    return _FakeOrchestrator()


@pytest.fixture()
def test_app(
    fake_orchestrator: _FakeOrchestrator, monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    """Create a FastAPI app with overridden dependencies for testing."""

    app = FastAPI()
    app.include_router(chat_runtime.router)

    app.dependency_overrides[chat_runtime.get_chat_orchestrator] = lambda: fake_orchestrator
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


def test_chat_runtime_returns_response(
    test_app: TestClient, fake_orchestrator: _FakeOrchestrator
) -> None:
    """The non-streaming chat runtime route should return a JSON payload."""

    response = test_app.post(
        "/chat/runtime",
        json={
            "message": "Hello",
            "provider": "user-provider",
            "model": "user-model",
            "temperature": 0.25,
            "max_tokens": 256,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["content"] == "Hello world"
    assert payload["metadata"]["kire_metadata"]["provider"] == "test-provider"
    assert payload["metadata"]["requested_generation"]["provider"] == "user-provider"
    assert payload["metadata"]["requested_generation"]["model"] == "user-model"
    assert payload["metadata"]["requested_generation"]["temperature"] == 0.25
    assert payload["metadata"]["requested_generation"]["max_tokens"] == 256
    assert fake_orchestrator.calls
    last_call = fake_orchestrator.calls[-1]
    assert last_call.metadata.get("preferred_llm_provider") == "user-provider"
    assert last_call.metadata.get("preferred_model") == "user-model"
    assert last_call.metadata["requested_generation"]["temperature"] == 0.25


def test_chat_runtime_stream_emits_tokens(
    test_app: TestClient, fake_orchestrator: _FakeOrchestrator
) -> None:
    """The streaming chat runtime route should emit SSE token events."""

    with test_app.stream(
        "POST",
        "/chat/runtime/stream",
        json={
            "message": "Stream please",
            "provider": "user-provider",
            "model": "user-model",
        },
    ) as response:
        # Collect the streamed lines so json.dumps is exercised
        lines = list(response.iter_lines())

    assert response.status_code == 200
    # Ensure at least one token and completion event were emitted
    assert any("\"type\": \"token\"" in line for line in lines)
    assert any("\"type\": \"complete\"" in line for line in lines)
    metadata_lines = [line for line in lines if '"type": "metadata"' in line]
    assert metadata_lines
    metadata_payload = json.loads(metadata_lines[0].split("data: ", 1)[1])
    assert (
        metadata_payload["data"]["requested_generation"]["provider"]
        == "user-provider"
    )
    assert fake_orchestrator.calls
    last_call = fake_orchestrator.calls[-1]
    assert last_call.metadata.get("preferred_llm_provider") == "user-provider"


def test_chat_runtime_stream_handles_missing_kire(
    test_app: TestClient, fake_orchestrator: _FakeOrchestrator, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Streaming should still work if the routing engine returns no decision."""

    monkeypatch.setattr(chat_runtime, "get_registry", lambda: _NoDecisionRegistry())

    with test_app.stream(
        "POST",
        "/chat/runtime/stream",
        json={
            "message": "Stream please",
            "provider": "user-provider",
        },
    ) as response:
        lines = list(response.iter_lines())

    assert response.status_code == 200
    metadata_lines = [line for line in lines if '"type": "metadata"' in line]
    assert metadata_lines, "Expected at least one metadata event"
    payload = json.loads(metadata_lines[0].split("data: ", 1)[1])
    assert "kire" not in payload["data"]
    assert payload["data"]["requested_generation"]["provider"] == "user-provider"
    assert fake_orchestrator.calls
    last_call = fake_orchestrator.calls[-1]
    assert last_call.metadata.get("preferred_llm_provider") == "user-provider"


def test_chat_runtime_response_core_round_trip(
    test_app: TestClient,
    fake_orchestrator: _FakeOrchestrator,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The response-core route should return prompt output when available."""

    fake_orchestrator = _FakeResponseCoreOrchestrator()
    monkeypatch.setattr(
        chat_runtime,
        "get_global_orchestrator",
        lambda user_id: fake_orchestrator,
    )

    response = test_app.post(
        "/chat/runtime/response-core",
        json={"message": "Hello core"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["content"] == "Response core says hello"
    assert payload["metadata"]["orchestrator"] == "response_core"
    assert fake_orchestrator.calls  # ensure the orchestrator was invoked
    called_message, ui_caps = fake_orchestrator.calls[0]
    assert called_message == "Hello core"
    assert ui_caps["platform"] == "web"
