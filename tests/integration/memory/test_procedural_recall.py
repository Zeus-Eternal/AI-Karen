from ai_karen_engine.core.memory.neuro.procedural_memory import ProceduralMemoryStore, default_routing_procedures

def test_procedural_recall_weather():
    s = ProceduralMemoryStore()
    for p in default_routing_procedures():
        s.put('t', p)
    assert s.recall('t', 'weather forecast')
