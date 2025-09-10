import pytest

from ai_karen_engine.integrations.task_analyzer import TaskAnalyzer


def test_task_analyzer_basic_classification():
    ta = TaskAnalyzer()
    a = ta.analyze("please summarize this text")
    assert a.task_type == "summarization"
    assert "text" in a.required_capabilities
    assert a.khrp_step_hint == "output_rendering"

    a2 = ta.analyze("why is the sky blue? explain the logic")
    assert a2.task_type == "reasoning"
    assert "reasoning" in a2.required_capabilities
    assert a2.khrp_step_hint == "reasoning_core"

    a3 = ta.analyze("write python code to add two numbers")
    assert a3.task_type == "code"
    assert set(["text", "code"]).issubset(set(a3.required_capabilities))

