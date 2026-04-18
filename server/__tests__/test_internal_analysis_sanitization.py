from ai_karen_engine.chat.ChatOrchestrator.mixins.core_mixin import ChatCoreMixin


def test_strip_internal_analysis_block_when_appended():
    content = (
        "Hello! How can I help with your project today?\n\n"
        "===\n"
        "Since the user has greeted again without a specific new request, I'll acknowledge their greeting.\n\n"
        "In summary:\n\n"
        "This is NOT a complete meaningful response, the summary is cut off.\n"
    )

    cleaned = ChatCoreMixin._strip_internal_analysis_leakage(content)

    assert cleaned == "Hello! How can I help with your project today?"


def test_strip_internal_analysis_only_content_to_empty():
    content = (
        "===\n"
        "Since the user has greeted again without a specific new request, I'll acknowledge their greeting.\n"
        "In summary:\n"
        "This is NOT a complete meaningful response, the summary is cut off.\n"
    )

    cleaned = ChatCoreMixin._strip_internal_analysis_leakage(content)

    assert cleaned == ""


def test_preserve_normal_summary_text():
    content = "In summary:\nUse a single DB transaction and return early on validation errors."

    cleaned = ChatCoreMixin._strip_internal_analysis_leakage(content)

    assert cleaned == content
