import asyncio
import json
import os
import sys
from typing import Any, Tuple


async def run_in_sandbox(module: str, params: dict, timeout: float = 5.0, cpu_seconds: int = 2) -> Tuple[Any, str, str]:
    """Execute plugin handler in isolated subprocess."""
    cmd = [sys.executable, "-m", "src.extensions.plugins.core.sandbox_runner", module]
    env = {
        "KARI_CPU_LIMIT": str(cpu_seconds),
        "PYTHONPATH": os.pathsep.join(sys.path),
    }
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    data = json.dumps(params).encode()
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(data), timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise TimeoutError(f"Plugin '{module}' timed out")
    out_text = stdout.decode()
    err_text = stderr.decode()
    if proc.returncode != 0:
        raise RuntimeError(err_text or f"Plugin '{module}' failed")
    result = json.loads(out_text) if out_text else None
    return result, out_text, err_text