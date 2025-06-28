from src.integrations.llm_utils import LLMUtils


def test_llm_utils_fallback():
    llm = LLMUtils(model_name="nonexistent-model")
    out = llm.generate_text("hello")
    assert "hello" in out
    assert llm.generator is None
