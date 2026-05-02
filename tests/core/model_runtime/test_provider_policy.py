from ai_karen_engine.core.model_runtime.provider_policy import evaluate_provider_policy


def test_ollama_is_local_provider_option():
    decision = evaluate_provider_policy("ollama", local_enabled=True)
    assert decision.allowed is True
    assert decision.classification == "local_provider_option"


def test_vllm_is_builtin_engine():
    decision = evaluate_provider_policy("vllm")
    assert decision.allowed is True
    assert decision.classification == "builtin_engine"


def test_local_gguf_removed():
    decision = evaluate_provider_policy("local_gguf", local_enabled=True, external_enabled=True)
    assert decision.allowed is False
    assert decision.reason == "removed_internal_provider"
