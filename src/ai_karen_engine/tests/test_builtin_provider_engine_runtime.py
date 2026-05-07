import pytest

from ai_karen_engine.core.expression.engines.builtin_provider_engine import BuiltinProviderEngine
from ai_karen_engine.core.expression.contracts import ExpressionTask
from ai_karen_engine.inference.transformers_runtime import TransformersRuntime
from ai_karen_engine.integrations.llm_utils import ProviderNotAvailable


class _DummyProvider:
    def __init__(self, text, model="auto"):
        self._text=text
        self.model=model
    def generate_text(self, prompt, **kwargs):
        return self._text


@pytest.mark.asyncio
async def test_builtin_engine_vllm_failure_falls_back_to_transformers_with_attempts(monkeypatch):
    def _get_provider(pid, model=None):
        if pid == "builtin_vllm":
            raise ProviderNotAvailable("down")
        return _DummyProvider("transformers live proof", model="gpt2")

    monkeypatch.setattr("ai_karen_engine.integrations.llm_registry.get_provider", _get_provider)
    engine = BuiltinProviderEngine()
    task = ExpressionTask(task_id="t1", kind="chat", messages=[{"content":"hi"}], response_mode="chat", required_capabilities=["chat"], forbidden_capabilities=[], request_id="r1", correlation_id="c1", preferred_provider="builtin_vllm", preferred_model="auto")
    result = await engine.generate(task)
    assert result.text == "transformers live proof"
    assert result.provider == "builtin_transformers"
    assert result.runtime_engine == "transformers"
    assert result.metadata["response_source"] == "fallback_provider_runtime"
    assert any(a["status"] == "failed" for a in result.metadata["provider_attempts"])


def test_transformers_runtime_raises_when_no_real_generation_available():
    runtime = TransformersRuntime()
    runtime._transformers_available = False
    runtime._pipeline = None
    with pytest.raises(ProviderNotAvailable):
        runtime.generate("hello")


@pytest.mark.asyncio
async def test_builtin_engine_returns_emergency_static_text_when_all_fail(monkeypatch):
    def _get_provider(pid, model=None):
        raise ProviderNotAvailable("down")

    monkeypatch.setattr("ai_karen_engine.integrations.llm_registry.get_provider", _get_provider)
    engine = BuiltinProviderEngine()
    task = ExpressionTask(task_id="t2", kind="chat", messages=[{"content":"hi"}], response_mode="chat", required_capabilities=["chat"], forbidden_capabilities=[], preferred_provider="builtin_transformers", preferred_model="auto")
    result = await engine.generate(task)
    assert result.response_source == "emergency_static"
    assert result.provider is None
    assert "No configured built-in provider" in result.text


@pytest.mark.asyncio
async def test_disabled_engine_reports_emergency_static_metadata():
    from ai_karen_engine.core.expression.engines.disabled_engine import DisabledEngine
    task = ExpressionTask(task_id="t3", kind="chat", messages=[{"content":"hi"}], response_mode="chat", required_capabilities=["chat"], forbidden_capabilities=[])
    result = await DisabledEngine().generate(task)
    assert result.response_source == "emergency_static"
    assert result.provider is None
    assert result.metadata["fallback_level"] == 99


def test_transformers_runtime_attempts_warm_before_failing(monkeypatch):
    runtime = TransformersRuntime()
    runtime._transformers_available = True
    runtime._pipeline = None

    called = {"warm": 0}
    def _warm(_model_path=None):
        called["warm"] += 1
        return False

    monkeypatch.setattr(runtime, "warm", _warm)

    with pytest.raises(Exception):
        runtime.generate("hello")

    assert called["warm"] == 1
