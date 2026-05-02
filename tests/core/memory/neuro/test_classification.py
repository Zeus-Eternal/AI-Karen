from ai_karen_engine.core.memory.neuro.contracts import MemoryCandidate, MemoryClass
from ai_karen_engine.core.memory.neuro.classification import classify_memory_candidate


def _candidate(text: str):
    return MemoryCandidate(id='1', text=text, memory_class=MemoryClass.EPISODIC, source='conversation', tenant_id='t', user_id='u')


def test_semantic_fact_classification():
    assert classify_memory_candidate(_candidate("My favorite color is green")).value == 'semantic'
