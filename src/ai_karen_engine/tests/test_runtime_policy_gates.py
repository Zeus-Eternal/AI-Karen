import pytest

from ai_karen_engine.core.cortex.kire_kro_integration import KIREKROIntegration
from ai_karen_engine.core.cortex.runtime_policy import RuntimePolicyDecision


def test_runtime_policy_decision_defaults():
    decision = RuntimePolicyDecision.from_cortex({})
    assert decision.requires_deep_reasoning is False
    assert decision.requires_medusa is False
    assert decision.policy_token


def test_runtime_policy_decision_from_cortex_flags():
    decision = RuntimePolicyDecision.from_cortex(
        {"requires_deep_reasoning": True, "requires_medusa": True}
    )
    assert decision.requires_deep_reasoning is True
    assert decision.requires_medusa is True


@pytest.mark.asyncio
async def test_simple_chat_policy_bypasses_langgraph_and_medusa(monkeypatch):
    integration = KIREKROIntegration()

    async def _fake_init():
        integration._initialized = True

    monkeypatch.setattr(integration, "initialize", _fake_init)

    class _FakeOrchestrator:
        async def process(self, **kwargs):  # pragma: no cover
            raise AssertionError("LangGraph should not be called for simple chat policy")

    async def _fake_medusa_node(state):  # pragma: no cover
        raise AssertionError("Medusa should not be called for simple chat policy")

    monkeypatch.setattr(
        "ai_karen_engine.core.langgraph_orchestrator.LangGraphOrchestrator",
        _FakeOrchestrator,
    )
    monkeypatch.setattr(
        "ai_karen_engine.core.cortex.kire_kro_integration.medusa_node",
        _fake_medusa_node,
    )

    result = await integration.process_user_request(
        "hello",
        context={"cortex_policy": {"requires_deep_reasoning": False, "requires_medusa": False}},
    )
    assert result["success"] is True
    assert result["meta"]["execution_path"] == "standard"
