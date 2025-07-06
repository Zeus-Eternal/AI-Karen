import os
import subprocess
import asyncio
from typing import Dict, Any


async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    branch = params.get("branch", "main")
    repo = params.get("repo", ".")
    env = os.environ.copy()
    try:
        await asyncio.to_thread(
            subprocess.check_call,
            ["git", "rev-parse", "--verify", branch],
            cwd=repo,
        )
        await asyncio.to_thread(
            subprocess.check_call,
            ["git", "merge", branch],
            cwd=repo,
            env=env,
        )
    except FileNotFoundError:
        return {"error": "git_not_found"}
    except subprocess.CalledProcessError as exc:
        return {"error": "git_merge_failed", "details": str(exc)}
    return {"status": "merged", "branch": branch}
