from ai_karen_engine.core.cortex.routing_intents import (
    CAPABILITY_ROUTES,
    get_capability_routes,
    resolve_capability_decision,
)


def test_capability_registry_contains_live_fact_routes():
    assert "time.current" in CAPABILITY_ROUTES
    assert "web.search" in CAPABILITY_ROUTES
    assert "weather.current" in CAPABILITY_ROUTES


def test_time_query_requires_tool():
    decision = resolve_capability_decision("What time is it in Detroit?")
    assert decision.intent == "time.current"
    assert decision.requires_tool is True
    assert decision.allow_llm_only is False
    assert decision.preferred_plugin == "time-query"


def test_web_search_requires_tool_and_live_data():
    decision = resolve_capability_decision("Search the internet for latest vLLM CUDA issue")
    assert decision.intent == "web.search"
    assert decision.requires_tool is True
    assert decision.requires_live_data is True
    assert decision.capability == "web_search"


def test_general_chat_allows_llm_only():
    decision = resolve_capability_decision("Tell me a joke")
    assert decision.intent == "general.chat"
    assert decision.requires_tool is False
    assert decision.allow_llm_only is True


def test_dynamic_capability_route_discovery_returns_routes():
    routes = get_capability_routes(force_refresh=True)
    assert "time.current" in routes
    assert "web.search" in routes
    assert routes["time.current"]["required_capability"] == CAPABILITY_ROUTES["time.current"]["required_capability"]
