from types import SimpleNamespace

import pytest

from ai_karen_engine.chat.chat_orchestrator import (
    ChatOrchestrator,
    LLMResponseVerificationError,
)
from ai_karen_engine.core.degraded_mode import get_degraded_mode_manager


@pytest.fixture()
def orchestrator():
    manager = get_degraded_mode_manager()
    original_status = manager.status.is_active
    manager.status.is_active = False
    try:
        yield ChatOrchestrator()
    finally:
        manager.status.is_active = original_status


def test_ensure_llm_response_is_valid_accepts_verified_provider(orchestrator):
    result = SimpleNamespace(
        content="ok",
        provider="openai",
        model_id="openai:gpt-4",
        tags=["primary"],
        is_degraded=False,
        attempted_models=["openai:gpt-4"],
        failure_reason=None,
        metadata={"mode": "text"},
    )

    orchestrator._ensure_llm_response_is_valid(result, "unit-test")


def test_ensure_llm_response_is_valid_rejects_degraded(orchestrator):
    degraded = SimpleNamespace(
        content="fallback",
        provider="degraded",
        model_id="degraded:fallback",
        tags=["degraded"],
        is_degraded=True,
        attempted_models=[],
        failure_reason="all providers failed",
        metadata={},
    )

    with pytest.raises(LLMResponseVerificationError):
        orchestrator._ensure_llm_response_is_valid(degraded, "unit-test")


def test_ensure_llm_response_is_valid_rejects_when_system_degraded(orchestrator):
    manager = get_degraded_mode_manager()
    manager.status.is_active = True
    try:
        healthy = SimpleNamespace(
            content="hello",
            provider="openai",
            model_id="openai:gpt-4",
            tags=["primary"],
            is_degraded=False,
            attempted_models=["openai:gpt-4"],
            failure_reason=None,
            metadata={},
        )

        with pytest.raises(LLMResponseVerificationError):
            orchestrator._ensure_llm_response_is_valid(healthy, "unit-test")
    finally:
        manager.status.is_active = False


def test_build_llm_metadata_includes_source_and_extra(orchestrator):
    result = SimpleNamespace(
        content="hello",
        provider="openai",
        model_id="openai:gpt-4",
        tags=["primary"],
        is_degraded=False,
        attempted_models=["openai:gpt-4"],
        failure_reason=None,
        metadata={"mode": "text"},
    )

    metadata = orchestrator._build_llm_metadata(
        result,
        "unit-test",
        additional={"extra_field": "value"},
    )

    assert metadata["provider"] == "openai"
    assert metadata["model_id"] == "openai:gpt-4"
    assert metadata["source"] == "unit-test"
    assert metadata["extra"]["mode"] == "text"
    assert metadata["extra_field"] == "value"
