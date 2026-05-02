from ai_karen_engine.core.memory.neuro.procedural_memory import default_routing_procedures


def test_default_procedures_include_weather_and_joke():
    names = [p.name for p in default_routing_procedures()]
    assert 'weather_via_web_search' in names
    assert 'joke_via_llm_only' in names
