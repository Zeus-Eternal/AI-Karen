from ai_karen_engine.core.memory.neuro.contracts import MemoryCandidate, MemoryClass
from ai_karen_engine.core.memory.neuro.consolidation import decide_consolidation


def test_repeated_episodic_promotes():
    c = MemoryCandidate(id='1', text='deadline', memory_class=MemoryClass.EPISODIC, source='conversation', tenant_id='t', user_id='u', metadata={'reuse_count': 3})
    d = decide_consolidation(c)
    assert d.promote
