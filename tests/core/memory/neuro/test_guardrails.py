from ai_karen_engine.core.memory.neuro.contracts import MemoryCandidate, MemoryClass
from ai_karen_engine.core.memory.neuro.guardrails import evaluate_guardrails


def test_quarantine_untrusted_web():
    c = MemoryCandidate(id='1', text='info', memory_class=MemoryClass.SEMANTIC, source='web', tenant_id='t', user_id='u', metadata={'source_trust': 0.2})
    d = evaluate_guardrails(c)
    assert d.outcome.value in {'quarantine', 'reject', 'requires_review', 'allow'}
