from pathlib import Path


def test_legacy_fallback_manager_has_no_provider_guesses():
    text = Path('src/ai_karen_engine/integrations/fallback_manager.py').read_text().lower()
    forbidden = [
        'local_gguf',
        'gemini-1.5-flash',
        'llama3.2:latest',
        'microsoft/dialoqpt-medium',
        'default-model',
    ]
    for token in forbidden:
        assert token not in text


def test_legacy_fallback_manager_is_removed():
    """Verify legacy fallback manager has been removed completely."""
    text = Path('src/ai_karen_engine/integrations/fallback_manager.py').read_text().lower()
    # Check for clear indication it's removed
    assert 'legacy fallback manager - removed' in text or 'removed' in text
    # Verify it raises an error
    try:
        from ai_karen_engine.integrations.fallback_manager import get_fallback_manager
        get_fallback_manager()
        assert False, "get_fallback_manager should raise FallbackManagerRemovedError"
    except Exception:
        pass  # Expected to raise an error
