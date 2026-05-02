from ai_karen_engine.services.models.routing.llm_router_service import ProviderProcessingError


def test_provider_processing_error_accepts_error_list():
    err = ProviderProcessingError("ollama", [RuntimeError("boom")])
    assert "ollama failed after" in str(err)
    assert err.last_error is not None
