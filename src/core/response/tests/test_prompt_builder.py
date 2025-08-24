"""Tests for the Jinja2 prompt building utilities."""

from __future__ import annotations

from src.core.response import (
    PipelineConfig,
    PromptBuilder,
    ResponseOrchestrator,
    UnifiedLLMClient,
)


def _builder() -> PromptBuilder:
    """Create a ``PromptBuilder`` using the default template directory."""

    return PromptBuilder(PipelineConfig().template_dir)


def test_render_core_templates() -> None:
    builder = _builder()
    assert builder.system_base("assistant") == "You are assistant."
    assert builder.user_frame("hello") == "hello"
    gaps = ["email", "location"]
    expected = "Please provide the following information: email, location."
    assert builder.onboarding(gaps) == expected


def test_build_full_prompt_with_context_and_gaps() -> None:
    builder = _builder()
    prompt = builder.build(
        persona="helper",
        user_input="final message",
        context=["msg1", "msg2"],
        profile_gaps=["age"],
        system_prompts=["SYS"],
    )
    expected = (
        "SYS\n"
        "You are helper.\n"
        "msg1\n"
        "msg2\n"
        "final message\n"
        "Please provide the following information: age."
    )
    assert prompt == expected


class _StubAnalyzer:
    def analyze(self, _: str) -> dict[str, object]:
        return {"persona": "guide", "profile_gaps": ["email"]}


class _StubMemory:
    def __init__(self) -> None:
        self.saved: list[tuple[str, str, str]] = []

    def fetch_context(self, _: str) -> list[str]:
        return ["previous"]

    def store(self, cid: str, user_input: str, response: str) -> None:
        self.saved.append((cid, user_input, response))


class _CaptureLLM:
    def __init__(self) -> None:
        self.last_prompt: str = ""

    def generate(self, prompt: str, **_: str) -> str:
        self.last_prompt = prompt
        return "ok"


def test_orchestrator_uses_prompt_builder_for_full_prompt() -> None:
    analyzer = _StubAnalyzer()
    memory = _StubMemory()
    llm = _CaptureLLM()
    orchestrator = ResponseOrchestrator(
        PipelineConfig(system_prompts=["SYS"]),
        analyzer,
        memory,
        UnifiedLLMClient(llm),
    )
    orchestrator.respond("cid", "hello")
    expected = (
        "SYS\n"
        "You are guide.\n"
        "previous\n"
        "hello\n"
        "Please provide the following information: email."
    )
    assert llm.last_prompt == expected
