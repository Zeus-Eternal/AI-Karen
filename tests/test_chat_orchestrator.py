import pytest
from ai_karen_engine.chat.chat_orchestrator import (
    ChatOrchestrator,
    ChatRequest,
    RetryConfig,
    ProcessingResult,
)


class DummyParsed:
    entities = []


@pytest.mark.asyncio
async def test_process_message_success(monkeypatch):
    orch = ChatOrchestrator(retry_config=RetryConfig(max_attempts=1))

    async def fake_process(req, ctx):
        return ProcessingResult(
            success=True,
            response="hello",
            parsed_message=DummyParsed(),
            embeddings=[0.1],
            context={},
            correlation_id=ctx.correlation_id,
        )

    monkeypatch.setattr(orch, "_process_with_retry", fake_process)

    req = ChatRequest(message="hi", user_id="u", conversation_id="c", stream=False)
    resp = await orch.process_message(req)
    assert resp.response == "hello"
    assert resp.used_fallback is False
    assert resp.context_used is False


@pytest.mark.asyncio
async def test_process_message_failure(monkeypatch):
    orch = ChatOrchestrator(retry_config=RetryConfig(max_attempts=1))

    async def fake_process(req, ctx):
        return ProcessingResult(
            success=False,
            error="boom",
            error_type=None,
            correlation_id=ctx.correlation_id,
        )

    monkeypatch.setattr(orch, "_process_with_retry", fake_process)

    req = ChatRequest(message="hi", user_id="u", conversation_id="c", stream=False)
    resp = await orch.process_message(req)
    assert "error" in resp.response.lower()
    assert resp.used_fallback is True
