from ai_karen_engine.core.cortex.runtime_policy import RuntimePolicyDecision
from ai_karen_engine.core.cortex.kire_kro_integration import KIREKROIntegration


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


def test_simple_chat_policy_bypasses_langgraph_and_medusa():
    integration = KIREKROIntegration()
    decision = RuntimePolicyDecision.from_cortex({})
    assert decision.requires_deep_reasoning is False
    assert decision.requires_medusa is False
