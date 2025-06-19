import asyncio

from core.cortex.dispatch import CortexDispatcher


def test_dispatch_greet():
    dispatcher = CortexDispatcher()
    result = asyncio.run(dispatcher.dispatch("hello"))
    assert result["intent"] == "greet"
    assert result["response"] == "Hello World from plugin!"
