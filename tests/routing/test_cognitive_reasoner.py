from ai_karen_engine.integrations.task_analyzer import TaskAnalysis
from ai_karen_engine.routing.cognitive_reasoner import CognitiveReasoner
from ai_karen_engine.routing.types import RouteRequest


def test_cognitive_reasoner_honors_tool_bias_and_urgency():
    reasoner = CognitiveReasoner()
    request = RouteRequest(user_id="u1", task_type="chat", query="Run code now")
    analysis = TaskAnalysis(
        task_type="code",
        required_capabilities=["code"],
        hints={"secondary_tasks": ["reasoning"]},
        confidence=0.82,
        tool_intents=["code_execution", "web_browse"],
        user_need_state={"urgency": "high", "affect": "stressed", "mode": "problem_solving"},
    )

    cognition = reasoner.evaluate(request, analysis, profile=None)

    assert cognition.primary_goal == "code"
    assert "code_execution" in cognition.recommended_tools
    assert cognition.need_urgency == "high"
    assert "secondary=reasoning" in cognition.narrative
    assert cognition.decision_vector["urgency_weight"] > cognition.decision_vector["affect_weight"]


def test_cognitive_reasoner_infers_persona_from_context():
    reasoner = CognitiveReasoner()
    request = RouteRequest(
        user_id="u2",
        task_type="chat",
        query="Just curious",
        context={"persona": "creative"},
    )
    analysis = TaskAnalysis(
        task_type="chat",
        required_capabilities=["text"],
        confidence=0.6,
        tool_intents=[],
        user_need_state={"urgency": "normal", "affect": "curious", "mode": "informational"},
    )

    cognition = reasoner.evaluate(request, analysis, profile=None)

    assert cognition.persona_bias == "creative"
    assert cognition.decision_vector["persona_alignment"] >= 0.1
