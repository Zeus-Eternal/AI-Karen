from ..src.ai_karen_engine.clients.slm_pool import SLMPool
from integrations.llm_utils import LLMUtils


def test_slm_pool_register_and_get():
    pool = SLMPool()
    model = LLMUtils(model_name="nonexistent-model")
    pool.register("summarizer", model)
    assert pool.get("summarizer") is model
    assert "summarizer" in list(pool.skills())
