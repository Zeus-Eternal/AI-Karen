from pathlib import Path


def test_local_gguf_not_allowed_in_live_fallback_set():
    text = Path('src/ai_karen_engine/services/models/routing/llm_router_service.py').read_text().lower()
    assert 'allowed_live_fallback_providers' in text
    assert 'local_gguf' not in text[text.find('allowed_live_fallback_providers'):text.find('}', text.find('allowed_live_fallback_providers'))]


def test_degraded_provider_name_uses_requested_provider():
    text = Path('src/ai_karen_engine/services/models/routing/llm_router_service.py').read_text()
    assert 'provider_name = str(getattr(request, "preferred_provider", "") or "provider")' in text
