from pathlib import Path

def test_no_placeholder_in_router():
    text = Path('src/ai_karen_engine/core/memory/retrieval/retrieval_router.py').read_text().lower()
    assert 'placeholder' not in text
