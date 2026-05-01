from ai_karen_engine.services.response import ResponseSanitizer


def test_response_synthesis_no_leakage():
    leaked = """[transformers:auto]\nYou are Karen, a helpful assistant.\nAnswer only.\nUser's latest message: hi\nAssistant:\nHello there!"""
    response_text = ResponseSanitizer().sanitize(leaked)

    assert "You are Karen" not in response_text
    assert "Answer only" not in response_text
    assert "Do not" not in response_text
    assert "Assistant:" not in response_text
    assert "[transformers" not in response_text.lower()
    assert response_text == "Hello there!"
