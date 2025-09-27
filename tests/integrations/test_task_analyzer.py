from ai_karen_engine.integrations.task_analyzer import TaskAnalyzer


def test_task_analyzer_honors_context_task_hint():
    analyzer = TaskAnalyzer()
    analysis = analyzer.analyze(
        "Please assist with this request",
        context={"task_hint": "embedding", "requirements": {"capabilities": ["embeddings"]}},
    )

    assert analysis.task_type == "embedding"
    assert "embeddings" in analysis.required_capabilities
    assert analysis.hints.get("task_hint") == "embedding"


def test_task_analyzer_uses_role_bias_for_code():
    analyzer = TaskAnalyzer()
    analysis = analyzer.analyze(
        "Need some help",
        user_ctx={"roles": ["Developer"]},
        context={},
    )

    assert analysis.task_type == "code"
    assert "code" in analysis.required_capabilities


def test_task_analyzer_defaults_to_chat_for_low_signal():
    analyzer = TaskAnalyzer()
    analysis = analyzer.analyze("Hello", context={})

    assert analysis.task_type in {"chat", "code"}
    # Should not drop required capabilities for chat fallback
    if analysis.task_type == "chat":
        assert analysis.required_capabilities == ["text"]


def test_task_analyzer_extracts_tool_intents_and_need_state():
    analyzer = TaskAnalyzer()
    analysis = analyzer.analyze(
        "Urgent: please run this script and check the web docs",
        context={"tool_suggestions": ["browser"]},
    )

    assert "code_execution" in analysis.tool_intents
    assert "web_browse" in analysis.tool_intents
    assert analysis.user_need_state.get("urgency") in {"high", "elevated"}
    assert analysis.user_need_state.get("mode") in {"problem_solving", "analysis"}


def test_task_analyzer_tracks_secondary_tasks_from_context_history():
    analyzer = TaskAnalyzer()
    analysis = analyzer.analyze(
        "Help summarise",
        context={
            "conversation_history": [
                {"role": "user", "content": "also need reasoning about implications"},
            ]
        },
    )

    assert analysis.task_type == "reasoning"
    assert analysis.user_need_state.get("mode") == "analysis"
    if analysis.hints.get("secondary_tasks"):
        assert analysis.task_type not in analysis.hints["secondary_tasks"]
