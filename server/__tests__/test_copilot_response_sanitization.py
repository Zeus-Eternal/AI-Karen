from ai_karen_engine.api_routes.copilot_routes import (
    _is_placeholder_response,
    _sanitize_user_visible_text,
)


def test_short_greeting_is_not_placeholder():
    assert _is_placeholder_response("Hi") is False
    assert _is_placeholder_response("Thanks!") is False


def test_degraded_shim_prefix_is_placeholder():
    content = (
        "I understand you're asking about: hi. "
        "I'm currently operating with limited capabilities."
    )
    assert _is_placeholder_response(content) is True


def test_sanitize_strips_internal_analysis_scaffold():
    content = (
        "Hello! How can I help with your project today?\n\n"
        "===\n"
        "Since the user has greeted again without a specific new request, I'll acknowledge their greeting.\n\n"
        "In summary:\n\n"
        "This is NOT a complete meaningful response, the summary is cut off.\n"
    )

    cleaned = _sanitize_user_visible_text(content)

    assert cleaned == "Hello! How can I help with your project today?"

