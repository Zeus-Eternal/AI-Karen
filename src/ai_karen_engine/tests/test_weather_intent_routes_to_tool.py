from pathlib import Path


def test_weather_intent_routes_to_tool():
    decision_engine_file = Path(__file__).resolve().parents[2] / "ai_karen_engine" / "core" / "langgraph_orchestrator" / "decision_engine.py"
    text = decision_engine_file.read_text(encoding="utf-8", errors="ignore")

    assert '"weather_query": ["web_search"]' in text
