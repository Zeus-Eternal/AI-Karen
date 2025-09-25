import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_karen_engine.chat.chat_orchestrator import (
    ChatOrchestrator,
    ChatRequest,
    ChatResponse,
    ChatStreamChunk,
    RetryConfig,
    ProcessingResult,
)
from ai_karen_engine.hooks import HookTypes
from ai_karen_engine.hooks.models import HookExecutionSummary


class DummyParsed:
    """Minimal parsed message used in fake processing results."""

    entities = []


@pytest.fixture(params=["base", "hooks", "memory"])
def orchestrator(request):
    """Create a ChatOrchestrator for different integration contexts."""

    if request.param == "memory":
        from ai_karen_engine.chat.memory_processor import MemoryProcessor

        memory = MagicMock(spec=MemoryProcessor)
        orch = ChatOrchestrator(memory_processor=memory, retry_config=RetryConfig(max_attempts=1))
    else:
        orch = ChatOrchestrator(retry_config=RetryConfig(max_attempts=1))

    summary = HookExecutionSummary(
        hook_type=HookTypes.PRE_MESSAGE,
        total_hooks=0,
        successful_hooks=0,
        failed_hooks=0,
        total_execution_time_ms=0.0,
        results=[],
    )
    hook_manager = AsyncMock()
    hook_manager.trigger_hooks.return_value = summary
    patcher = patch("ai_karen_engine.chat.chat_orchestrator.get_hook_manager", return_value=hook_manager)
    patcher.start()
    request.addfinalizer(patcher.stop)
    return orch


@pytest.mark.asyncio
async def test_process_message_success(orchestrator, monkeypatch):
    async def fake_process(req, ctx):
        return ProcessingResult(
            success=True,
            response="hello",
            parsed_message=DummyParsed(),
            embeddings=[0.1],
            context={},
            correlation_id=ctx.correlation_id,
        )

    monkeypatch.setattr(orchestrator, "_process_with_retry", fake_process)

    req = ChatRequest(message="hi", user_id="u", conversation_id="c", stream=False, metadata={})
    resp = await orchestrator.process_message(req)
    assert isinstance(resp, ChatResponse)
    assert resp.response == "hello"
    assert resp.used_fallback is False


@pytest.mark.asyncio
async def test_process_message_failure(orchestrator, monkeypatch):
    async def fake_process(req, ctx):
        return ProcessingResult(
            success=False,
            error="boom",
            error_type=None,
            correlation_id=ctx.correlation_id,
        )

    monkeypatch.setattr(orchestrator, "_process_with_retry", fake_process)

    req = ChatRequest(message="hi", user_id="u", conversation_id="c", stream=False, metadata={})
    resp = await orchestrator.process_message(req)
    assert "error" in resp.response.lower()
    assert resp.used_fallback is True


@pytest.mark.asyncio
async def test_streaming_response(orchestrator, monkeypatch):
    async def fake_process(req, ctx):
        return ProcessingResult(
            success=True,
            response="hello world",
            parsed_message=DummyParsed(),
            embeddings=[0.1],
            context={},
            correlation_id=ctx.correlation_id,
        )

    monkeypatch.setattr(orchestrator, "_process_with_retry", fake_process)

    req = ChatRequest(message="hi", user_id="u", conversation_id="c", stream=True, metadata={})
    stream = await orchestrator.process_message(req)
    chunks = [chunk async for chunk in stream]

    assert any(chunk.type == "content" for chunk in chunks)
    assert chunks[-1].type == "complete"


@pytest.mark.asyncio
async def test_retry_logic_with_exponential_backoff():
    retry_config = RetryConfig(max_attempts=3, backoff_factor=2.0, initial_delay=0.01, exponential_backoff=True)
    orchestrator = ChatOrchestrator(retry_config=retry_config)
    attempts = []

    async def failing_process(*args, **kwargs):
        attempts.append(time.time())
        if len(attempts) < 3:
            raise Exception("Temporary failure")
        return ProcessingResult(success=True, response="ok", correlation_id="cid")

    with patch.object(orchestrator, "_process_message_internal", side_effect=failing_process):
        with patch("ai_karen_engine.chat.chat_orchestrator.get_hook_manager") as get_hook:
            hook_manager = AsyncMock()
            summary = HookExecutionSummary(
                hook_type=HookTypes.PRE_MESSAGE,
                total_hooks=0,
                successful_hooks=0,
                failed_hooks=0,
                total_execution_time_ms=0.0,
                results=[],
            )
            hook_manager.trigger_hooks.return_value = summary
            get_hook.return_value = hook_manager
            resp = await orchestrator.process_message(
                ChatRequest(message="hi", user_id="u", conversation_id="c", stream=False, metadata={})
            )

    assert resp.response == "ok"
    assert len(attempts) == 3


@pytest.mark.asyncio
async def test_timeout_handling():
    orchestrator = ChatOrchestrator(retry_config=RetryConfig(max_attempts=1), timeout_seconds=0.1)

    async def slow_process(*args, **kwargs):
        await asyncio.sleep(0.2)
        return ProcessingResult(success=True, response="late", correlation_id="cid")

    with patch.object(orchestrator, "_process_message_internal", side_effect=slow_process):
        with patch("ai_karen_engine.chat.chat_orchestrator.get_hook_manager") as get_hook:
            hook_manager = AsyncMock()
            summary = HookExecutionSummary(
                hook_type=HookTypes.PRE_MESSAGE,
                total_hooks=0,
                successful_hooks=0,
                failed_hooks=0,
                total_execution_time_ms=0.0,
                results=[],
            )
            hook_manager.trigger_hooks.return_value = summary
            get_hook.return_value = hook_manager
            resp = await orchestrator.process_message(
                ChatRequest(message="hi", user_id="u", conversation_id="c", stream=False, metadata={})
            )

    assert "error" in resp.response.lower()
    assert resp.used_fallback is True


def test_processing_statistics():
    orchestrator = ChatOrchestrator()
    stats = orchestrator.get_processing_stats()
    assert stats["total_requests"] == 0

    orchestrator._total_requests = 5
    orchestrator._successful_requests = 3
    orchestrator._failed_requests = 2
    orchestrator._processing_times = [0.1, 0.2]

    stats = orchestrator.get_processing_stats()
    assert stats["successful_requests"] == 3
    assert stats["failed_requests"] == 2
    assert stats["success_rate"] == 0.6

