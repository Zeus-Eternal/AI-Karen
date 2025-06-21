from __future__ import annotations

"""DevOps capsule handler."""

from typing import Any, Dict


def run(message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    # For demonstration, simply echo deployment request
    branch = context.get("branch", "main")
    return {"action": "deploy", "branch": branch, "message": message}
