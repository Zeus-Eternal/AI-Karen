from src.ai_karen_engine import SLMPool, LLMOrchestrator
from src.integrations.llm_utils import LLMUtils


def test_orchestrator_uses_skill_model():
    pool = SLMPool()
    model = LLMUtils(model_name="nonexistent-model")
    pool.register("sentiment", model)
    orch = LLMOrchestrator(pool)
    out = orch.generate_text("hello", skill="sentiment")
    assert "hello" in out


def test_orchestrator_fallback_to_default():
    orch = LLMOrchestrator(SLMPool())
    out = orch.generate_text("fallback works")
    assert "fallback works" in out
