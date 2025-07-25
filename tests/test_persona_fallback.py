import pytest
from unittest.mock import Mock
from ai_karen_engine.services.ai_orchestrator.ai_orchestrator import AIOrchestrator
from ai_karen_engine.core.services.base import ServiceConfig
from ai_karen_engine.models.shared_types import FlowInput


@pytest.mark.asyncio
async def test_fallback_includes_persona_and_tone_when_provider_missing():
    orch = AIOrchestrator(ServiceConfig(name="test"))
    await orch.initialize()
    orch.llm_router.invoke = Mock(
        side_effect=RuntimeError(
            "No provider for intent 'conversation_processing' and no fallback"
        )
    )
    flow_input = FlowInput(
        prompt="Hi",
        conversation_history=[],
        user_settings={
            "personality_tone": "formal",
            "custom_persona_instructions": "Professor Bot",
        },
    )
    out = await orch.conversation_processing_flow(flow_input)
    assert "Professor Bot" in out.response
    assert "formal" in out.response
