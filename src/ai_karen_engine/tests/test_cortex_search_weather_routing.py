from ai_karen_engine.core.cortex.routing_intents import (
    CAPABILITY_ROUTES,
    extract_routing_parameters,
    resolve_capability_decision,
)


def test_weather_routes_to_internet_search():
    decision = resolve_capability_decision("What's the weather in Westland, MI?")
    assert decision.intent == "search.weather"
    assert decision.capability == "internet_search"
    assert decision.preferred_plugin == "intelligent-search"
    assert decision.handler == "weather"


def test_weather_capability_contract_is_search_mode():
    route = CAPABILITY_ROUTES["search.weather"]
    assert route["required_capability"] == "internet_search"
    assert route["handler"] == "weather"


def test_legacy_local_gguf_not_detected_as_provider_hint():
    params = extract_routing_parameters("please use local_gguf")
    assert params["requested_provider"] is None
