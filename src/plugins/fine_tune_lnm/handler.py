from __future__ import annotations

from pathlib import Path

from src.core.echo_core import EchoCore


async def run(params: dict) -> str:
    """Fine-tune the user's LNM on recorded interactions."""
    user_id = params.get("user_id", "default")
    logs = Path(params.get("log_path", f"data/users/{user_id}/interactions.json"))
    epochs = int(params.get("epochs", 3))

    core = EchoCore(user_id)
    core.fine_tune(logs, epochs=epochs)
    return "fine_tune_complete"
