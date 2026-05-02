import pytest

from ai_karen_engine.core.expression.contracts import ExpressionTask
from ai_karen_engine.core.expression.gateway import ExpressionGateway
from ai_karen_engine.core.expression.settings import ExpressionSettings


@pytest.mark.asyncio
async def test_provider_swap_does_not_break_runtime():
    settings = ExpressionSettings(active_engine="builtin")
    gateway = ExpressionGateway(settings=settings)

    task = ExpressionTask(
        task_id="t3",
        kind="chat",
        messages=[{"role": "user", "content": "test"}],
        response_mode="chat",
        required_capabilities=[],
        forbidden_capabilities=[],
        preferred_provider="builtin_transformers",
        metadata={"builtin_adapter": lambda payload: {"text": "first", "provider": "builtin_transformers"}},
    )
    first = await gateway.generate(task)

    swapped_task = ExpressionTask(
        task_id="t4",
        kind="chat",
        messages=[{"role": "user", "content": "test"}],
        response_mode="chat",
        required_capabilities=[],
        forbidden_capabilities=[],
        preferred_provider="openai",
        metadata={"builtin_adapter": lambda payload: {"text": "second", "provider": "openai"}},
    )
    second = await gateway.generate(swapped_task)

    assert first.text == "first"
    assert second.text == "second"
    assert second.provider == "openai"
