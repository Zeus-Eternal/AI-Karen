from pathlib import Path


def test_no_internal_gguf_provider_aliasing_in_chat_response():
    content = Path('src/ui_launchers/Karen-AI-Theme/src/lib/chat-response.ts').read_text()
    assert 'This provider is no longer available as a built-in runtime.' in content
    assert 'Configure llama.cpp/GGUF as a third-party endpoint if needed.' in content
