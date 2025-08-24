"""Tests for the :mod:`core.response` package."""

from core.response import PipelineConfig, ResponseOrchestrator


class DummyAnalyzer:
    def __init__(self) -> None:
        self.last_input: str | None = None

    def analyze(self, text: str) -> dict[str, str]:
        self.last_input = text
        return {"intent": "test"}


class DummyMemory:
    def __init__(self) -> None:
        self.fetch_called_with: str | None = None
        self.store_calls: list[tuple[str, str, str]] = []

    def fetch_context(self, conversation_id: str) -> list[str]:
        self.fetch_called_with = conversation_id
        return ["hi"]

    def store(self, conversation_id: str, user_input: str, response: str) -> None:
        self.store_calls.append((conversation_id, user_input, response))


class DummyLLM:
    def __init__(self) -> None:
        self.last_prompt: str | None = None

    def generate(self, prompt: str, **kwargs: object) -> str:
        self.last_prompt = prompt
        return "response"


def test_orchestrator_flow() -> None:
    config = PipelineConfig(system_prompts=["sys"])
    analyzer = DummyAnalyzer()
    memory = DummyMemory()
    llm = DummyLLM()
    orchestrator = ResponseOrchestrator(
        config=config,
        analyzer=analyzer,
        memory=memory,
        llm_client=llm,
    )

    result = orchestrator.respond("c1", "hello")
    assert result == "response"
    assert analyzer.last_input == "hello"
    assert memory.fetch_called_with == "c1"
    assert memory.store_calls == [("c1", "hello", "response")]
    assert llm.last_prompt is not None and "hello" in llm.last_prompt
    assert llm.last_prompt is not None and "hi" in llm.last_prompt
