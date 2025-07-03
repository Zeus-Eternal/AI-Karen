from __future__ import annotations

"""DevOps capsule handler executing git and k8s operations."""

import asyncio
from typing import Any, Dict

from src.core.plugin_router import PluginRouter

router = PluginRouter()


def run(message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    branch = context.get("branch", "main")
    deployment = context.get("deployment", "web")
    replicas = context.get("replicas", 1)

    async def _ops() -> None:
        await router.dispatch(
            "git_merge_safe",
            {"branch": branch, "repo": context.get("repo", ".")},
            roles=["devops"],
        )
        await router.dispatch(
            "k8s_scale",
            {"deployment": deployment, "replicas": replicas},
            roles=["devops"],
        )

    asyncio.run(_ops())

    return {
        "action": "deploy",
        "branch": branch,
        "deployment": deployment,
        "replicas": replicas,
        "message": message,
    }
