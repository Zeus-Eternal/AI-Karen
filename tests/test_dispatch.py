import asyncio
from core.cortex.dispatch import CortexDispatcher


def test_dispatch_greet():
    dispatcher = CortexDispatcher()
    result = asyncio.run(dispatcher.dispatch("hello", role="user"))
    assert result["intent"] == "greet"
    assert result["response"] == "Hello World from plugin!"


def test_dispatch_time_query():
    dispatcher = CortexDispatcher()
    result = asyncio.run(dispatcher.dispatch("the time"))
    assert result["intent"] == "time_query"
    assert "UTC" in result["response"]


def test_dispatch_fallback():
    dispatcher = CortexDispatcher()
    result = asyncio.run(dispatcher.dispatch("tell me something"))
    assert result["intent"] == "hf_generate"
    assert isinstance(result["response"], str)


def test_dispatch_deep_reasoning():
    dispatcher = CortexDispatcher()
    result = asyncio.run(dispatcher.dispatch("why do birds fly"))
    assert result["intent"] == "deep_reasoning"
    assert "entropy" in result["response"]
