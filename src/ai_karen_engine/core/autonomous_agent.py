"""Simple autonomous agent used for tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AutonomousAgent:
    """Minimal autonomous agent for workflow tests."""

    user_id: str
    llm: Any = field(default_factory=lambda: type("LLM", (), {"generate_text": lambda self, *_: ""})())
    prompt_router: Any = field(default_factory=lambda: type("Router", (), {"route": lambda self, _text: None})())
    workflow_engine: Any = field(default_factory=lambda: type("WF", (), {"trigger": lambda self, slug, payload: None})())
    automation_manager: Any = field(default_factory=lambda: type("AM", (), {"create_task": lambda self, **kw: None})())

    def think_and_act(self, goal: str, max_iterations: int = 1) -> None:
        """Execute a single reasoning loop."""
        steps = self.llm.generate_text(goal)
        plugin = self.prompt_router.route(steps)
        if plugin is None:
            return
        result = plugin.run({"subtask": steps})
        if plugin.manifest.get("enable_external_workflow"):
            self.workflow_engine.trigger(plugin.manifest["workflow_slug"], {"user_id": self.user_id})
        self.automation_manager.create_task(user_id=self.user_id, result=result)


__all__ = ["AutonomousAgent"]
