from src.core.autonomous_agent import AutonomousAgent


def test_agent_creates_task():
    agent = AutonomousAgent(user_id="u1")
    agent.think_and_act("organize files", max_iterations=1)
    assert agent.automation_manager.tasks
    task = agent.automation_manager.tasks[0]
    assert task["user_id"] == "u1"

