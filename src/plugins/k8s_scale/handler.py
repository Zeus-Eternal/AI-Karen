import subprocess
import asyncio
from typing import Dict, Any


async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    deployment = params.get("deployment")
    replicas = int(params.get("replicas", 1))
    namespace = params.get("namespace", "default")
    if not deployment:
        return {"error": "missing_deployment"}
    cmd = [
        "kubectl",
        "scale",
        "deployment",
        deployment,
        f"--replicas={replicas}",
        "-n",
        namespace,
    ]
    try:
        await asyncio.to_thread(subprocess.check_call, cmd)
    except FileNotFoundError:
        return {"error": "kubectl_not_found"}
    except subprocess.CalledProcessError as exc:
        return {"error": "scale_failed", "details": str(exc)}
    return {"status": "scaled", "deployment": deployment, "replicas": replicas}
