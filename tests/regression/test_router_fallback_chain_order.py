from pathlib import Path


def test_router_has_config_value_helper():
    text = Path('src/ai_karen_engine/services/models/routing/llm_router_service.py').read_text()
    assert 'def _get_config_value(' in text


def test_router_excludes_local_gguf_from_live_fallback_chain():
    text = Path('src/ai_karen_engine/services/models/routing/llm_router_service.py').read_text()
    assert 'if provider not in {"fallback", "local_gguf", failed_provider}' in text
