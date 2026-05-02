import pytest

from ai_karen_engine.core.expression.contracts import ExpressionTask
from ai_karen_engine.core.expression.engines.builtin_provider_engine import BuiltinProviderEngine


@pytest.mark.asyncio
async def test_builtin_engine_uses_adapter_response():
    engine = BuiltinProviderEngine()

    def adapter(payload):
        assert payload["provider"] == "builtin_vllm"
        return {"text": "hello", "provider": "builtin_vllm", "model": "phi-4"}

    task = ExpressionTask(
        task_id="t1",
        kind="chat",
        messages=[{"role": "user", "content": "hi"}],
        response_mode="chat",
        required_capabilities=[],
        forbidden_capabilities=[],
        preferred_provider="builtin_vllm",
        preferred_model="phi-4",
        metadata={"builtin_adapter": adapter},
    )

    result = await engine.generate(task)
    assert result.text == "hello"
    assert result.provider == "builtin_vllm"
    assert result.engine_id == "builtin"
