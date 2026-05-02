from ai_karen_engine.core.cortex.routing_intents import CAPABILITY_ROUTES

def test_weather_routes_to_search():
    assert CAPABILITY_ROUTES['search.weather']['handler'] == 'web_search'
