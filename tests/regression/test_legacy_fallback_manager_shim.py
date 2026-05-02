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


def test_legacy_fallback_manager_is_shim():
    text = Path('src/ai_karen_engine/integrations/fallback_manager.py').read_text().lower()
    assert 'compatibility shim' in text
