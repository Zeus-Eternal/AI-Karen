from ..src.ai_karen_engine.core.autonomous_agent import AutonomousAgent


def test_autonomous_agent(monkeypatch):
    agent = AutonomousAgent("u1")

    responses = iter(["steps", "subtask"])
    monkeypatch.setattr(agent.llm, "generate_text", lambda *_: next(responses))

    class DummyPlugin:
        manifest = {"enable_external_workflow": True, "workflow_slug": "slug"}

        def run(self, _):
            return {"message": "continue"}

    monkeypatch.setattr(agent.prompt_router, "route", lambda _: DummyPlugin())

    triggered = []
    monkeypatch.setattr(agent.workflow_engine, "trigger", lambda slug, payload: triggered.append(slug))

    tasks = []
    monkeypatch.setattr(agent.automation_manager, "create_task", lambda **kw: tasks.append(kw))

    monkeypatch.setattr("time.sleep", lambda *_: None)

    agent.think_and_act("goal", max_iterations=1)

    assert triggered == ["slug"]
    assert tasks and tasks[0]["user_id"] == "u1"

