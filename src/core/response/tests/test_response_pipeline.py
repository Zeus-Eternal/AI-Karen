import pytest

from src.core.response import PipelineConfig, ResponseOrchestrator, UnifiedLLMClient


class StubAnalyzer:
    def analyze(self, text: str):
        return {}


class StubMemory:
    def __init__(self):
        self.records = []

    def fetch_context(self, conversation_id: str):
        return []

    def store(self, conversation_id: str, user_input: str, response: str) -> None:
        self.records.append((conversation_id, user_input, response))


class StubLLMClient:
    def __init__(self, response: str, fail: bool = False):
        self.response = response
        self.fail = fail
        self.called_with = []

    def generate(self, prompt: str, model: str | None = None, **_: str) -> str:
        self.called_with.append(model)
        if self.fail:
            raise RuntimeError("failure")
        return f"{self.response} via {model}"


@pytest.fixture
def base_components():
    analyzer = StubAnalyzer()
    memory = StubMemory()
    return analyzer, memory


def test_orchestrator_uses_default_model(base_components):
    analyzer, memory = base_components
    primary = StubLLMClient("primary")
    orchestrator = ResponseOrchestrator(
        PipelineConfig(model="primary-model"),
        analyzer,
        memory,
        UnifiedLLMClient(primary),
    )
    result = orchestrator.respond("conv", "hi")
    assert result.endswith("primary via primary-model")
    assert primary.called_with[-1] == "primary-model"
    assert memory.records[0][2] == result


def test_orchestrator_falls_back_to_secondary_model(base_components):
    analyzer, memory = base_components
    primary = StubLLMClient("primary", fail=True)
    fallback = StubLLMClient("fallback")
    config = PipelineConfig(model="primary-model", fallback_model="secondary-model")
    orchestrator = ResponseOrchestrator(
        config,
        analyzer,
        memory,
        UnifiedLLMClient(primary, fallback),
    )
    result = orchestrator.respond("conv", "hi")
    assert result.endswith("fallback via secondary-model")
    assert primary.called_with[-1] == "primary-model"
    assert fallback.called_with[-1] == "secondary-model"
    assert memory.records[0][2] == result
