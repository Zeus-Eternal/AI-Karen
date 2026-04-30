from ai_karen_engine.core.runtime.chat_runtime_service import ChatRuntimeService


def _sample_payload():
    return {
        "answer": "hello from fallback",
        "metadata": {
            "llm": {
                "requested_provider": "openai",
                "requested_model": "gpt-4o",
                "actual_provider": "anthropic",
            }
        },
    }


def test_fallback_contract_identical_across_entrypoints():
    service = ChatRuntimeService()
    payload = _sample_payload()

    http_events = service.build_router_fallback_sse_events(payload, "cid-1")
    copilot_events = service.build_router_fallback_sse_events(payload, "cid-1")
    websocket_events = service.build_router_fallback_sse_events(payload, "cid-1")

    assert http_events == copilot_events == websocket_events
    assert any(event["type"] == "content" for event in http_events)
    assert http_events[-1]["type"] == "complete"
