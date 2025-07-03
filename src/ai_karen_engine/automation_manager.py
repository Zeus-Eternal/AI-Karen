"""Automation scheduler accessible via the ai_karen_engine namespace."""

class AutomationManager:
    """Simple scheduler for follow-up tasks."""

    def __init__(self) -> None:
        self.tasks = []

    def create_task(
        self,
        user_id: str,
        description: str,
        vevent_time: str,
        meta=None,
    ) -> dict:
        """Store a new task entry."""
        task = {
            "user_id": user_id,
            "description": description,
            "vevent_time": vevent_time,
            "meta": meta or {},
        }
        self.tasks.append(task)
        return task
