from pathlib import Path

def test_no_neuro_vault_in_ui_manager():
    text = Path('src/ai_karen_engine/services/ui/ag_ui_memory_manager.py').read_text()
    assert 'core.neuro_vault' not in text
