import pytest
from ai_karen_engine.core.model_runtime.provider_policy import evaluate_provider_policy

def test_builtin_engines_allowed():
    decision = evaluate_provider_policy("vllm")
    assert decision.allowed is True
    assert decision.classification == "builtin_engine"
    
    decision = evaluate_provider_policy("transformers")
    assert decision.allowed is True
    assert decision.classification == "builtin_engine"

def test_local_provider_options():
    # Test allowed when enabled
    decision = evaluate_provider_policy("ollama", local_enabled=True)
    assert decision.allowed is True
    assert decision.classification == "local_provider_option"
    
    # Test rejected when disabled
    decision = evaluate_provider_policy("ollama", local_enabled=False)
    assert decision.allowed is False
    assert decision.classification == "local_provider_option"
    assert decision.reason == "local_provider_disabled"

def test_external_provider_options():
    # Test allowed when enabled
    decision = evaluate_provider_policy("gemini", external_enabled=True)
    assert decision.allowed is True
    assert decision.classification == "external_provider_option"
    
    # Test rejected when disabled
    decision = evaluate_provider_policy("gemini", external_enabled=False)
    assert decision.allowed is False
    assert decision.classification == "external_provider_option"
    assert decision.reason == "external_provider_disabled"

def test_removed_internal_providers_rejected():
    removed_providers = [
        "gguf", "local_gguf", "llama_cpp", "llamacpp", "local", "default-model"
    ]
    for p in removed_providers:
        decision = evaluate_provider_policy(p)
        assert decision.allowed is False
        assert decision.classification == "removed_internal_provider"
        assert decision.reason == "removed_internal_provider"

def test_normalization():
    decision = evaluate_provider_policy("  Vllm  ")
    assert decision.provider == "vllm"
    assert decision.allowed is True
    
    decision = evaluate_provider_policy("llama-cpp")
    assert decision.provider == "llama_cpp"
    assert decision.classification == "removed_internal_provider"
