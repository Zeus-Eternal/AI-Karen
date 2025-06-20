import time
import uuid

from src.core.prompt_router import PromptRouter
from src.core.automation_manager import AutomationManager
from src.core.workflow_engine_client import WorkflowEngineClient
from src.integrations.llm_utils import LLMUtils


class AutonomousAgent:
    """Local-first autonomous agent loop."""

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self.prompt_router = PromptRouter()
        self.automation_manager = AutomationManager()
        self.workflow_engine = WorkflowEngineClient()
        self.llm = LLMUtils()

    def think_and_act(self, goal: str, context: str | None = None, max_iterations: int = 5) -> None:
        correlation_id = str(uuid.uuid4())
        print(f"[{correlation_id}] AutonomousAgent started for goal: {goal}")

        plan_prompt = f"You are a local agent. Break this goal into actionable steps: {goal}"
        steps = self.llm.generate_text(plan_prompt)
        print(f"[{correlation_id}] Plan: {steps}")

        for i in range(max_iterations):
            print(f"[{correlation_id}] Iteration {i + 1}")
            subtask = self.llm.generate_text(f"Based on: {steps}, which step to execute now?")
            print(f"[{correlation_id}] Next subtask: {subtask}")

            plugin = self.prompt_router.route(subtask)
            result = plugin.run(subtask)
            print(f"[{correlation_id}] Result: {result}")

            if plugin.manifest.get("enable_external_workflow"):
                slug = plugin.manifest.get("workflow_slug", "")
                self.workflow_engine.trigger(slug, result)

            time.sleep(2)

            if "DONE" in str(result.get("message", "")):
                print(f"[{correlation_id}] Goal accomplished!")
                break

            self.automation_manager.create_task(
                user_id=self.user_id,
                description=f"Follow-up for: {subtask}",
                vevent_time="next available",
                meta=result,
            )
