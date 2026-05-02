from pathlib import Path

def test_no_default_fallback_in_recall_context():
    text = Path('src/ai_karen_engine/core/memory/memory_runtime_manager.py').read_text()
    assert 'tenant_id=str(tenant_id or "default")' not in text
