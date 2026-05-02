from ai_karen_engine.core.memory.neuro.contracts import MemoryCandidate, MemoryClass
from ai_karen_engine.core.memory.neuro.decay_policy import decay_score


def test_decay_score_range():
    c = MemoryCandidate(id='1', text='x', memory_class=MemoryClass.SEMANTIC, source='conversation', tenant_id='t', user_id='u', confidence=0.9, importance=0.9)
    s = decay_score(c)
    assert 0.0 <= s <= 1.0
