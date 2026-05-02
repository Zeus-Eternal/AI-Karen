from ai_karen_engine.core.response.response_service import process_response


def test_process_response_includes_runtime_metadata_keys():
    out = process_response('hello world')
    assert 'preferred_engine' in out.metadata
    assert 'failed_providers' in out.metadata


def test_invalid_response_returns_unavailable_text():
    out = process_response('Assistant: leaked')
    assert out.valid is False
    assert out.text == 'Response unavailable.'
