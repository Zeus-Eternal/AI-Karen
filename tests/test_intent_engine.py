from core.intent_engine import IntentEngine


def test_detect_intent():
    engine = IntentEngine()
    cases = {
        "hello there": "greet",
        "hi": "greet",
        "ping": "greet",
      
        "why so sad": "deep_reasoning",
        "unknown text": "unknown",
        "HELLO": "greet",
    }
    for text, expected in cases.items():
        intent, conf, _ = engine.detect_intent(text)
        assert intent == expected
        assert 0.0 <= conf <= 1.0
