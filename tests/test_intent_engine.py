from ..src.ai_karen_engine.core.intent_engine import IntentEngine


def test_detect_intent():
    engine = IntentEngine()
    cases = {
        "hello there": "greet",
        "hi": "greet",
        "ping": "greet",
 

      
 
        "why so sad": "deep_reasoning",
        "what time is it": "time_query",
        "unknown text": "unknown",
        "HELLO": "greet",
    }
    for text, expected in cases.items():
        intent, conf, _ = engine.detect_intent(text)
        assert intent == expected
        assert 0.0 <= conf <= 1.0


def test_runtime_registration():
    engine = IntentEngine()
    engine.add_intent("farewell", r"bye")
    intent, _, _ = engine.detect_intent("bye")
    assert intent == "farewell"
    engine.remove_intent("farewell")
    intent, _, _ = engine.detect_intent("bye")
    assert intent == "unknown"
