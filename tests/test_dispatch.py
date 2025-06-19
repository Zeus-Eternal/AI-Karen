import asyncio

from core.cortex.dispatch import CortexDispatcher


def test_dispatch_greet():
    dispatcher = CortexDispatcher()
    result = asyncio.run(dispatcher.dispatch("hello"))
    assert result["intent"] == "greet"
    assert result["response"] == "Hello World from plugin!"


def test_dispatch_deep_reasoning():
    dispatcher = CortexDispatcher()
    result = asyncio.run(dispatcher.dispatch("why do birds fly"))
    assert result["intent"] == "deep_reasoning"
    assert "entropy" in result["response"]
