import pytest

from ai_karen_engine.core.expression.contracts import ExpressionTask
from ai_karen_engine.core.expression.engines.openai_compatible_engine import OpenAICompatibleEngine


@pytest.mark.asyncio
async def test_openai_compatible_engine_uses_adapter_response():
    engine = OpenAICompatibleEngine()

    def adapter(request):
        assert request["model"] == "gpt-4o-mini"
        return {"text": "ok", "provider": "openai", "model": "gpt-4o-mini"}

    task = ExpressionTask(
        task_id="t2",
        kind="chat",
        messages=[{"role": "user", "content": "hello"}],
        response_mode="chat",
        required_capabilities=[],
        forbidden_capabilities=[],
        preferred_model="gpt-4o-mini",
        metadata={"openai_compatible_adapter": adapter},
    )

    result = await engine.generate(task)
    assert result.text == "ok"
    assert result.provider == "openai"
