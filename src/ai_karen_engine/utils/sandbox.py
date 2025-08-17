from __future__ import annotations

import asyncio
import multiprocessing as mp
import resource
from typing import Any, Awaitable, Callable, Dict


def _target(handler: Callable[[Dict[str, Any]], Awaitable[Any]], params: Dict[str, Any], queue: mp.Queue, cpu: int, mem: int) -> None:
    """Execute handler with resource limits and send result through queue."""
    try:
        try:
            resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
        except Exception:
            pass
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
        except Exception:
            pass
        result = asyncio.run(handler(params))
        queue.put(("ok", result))
    except Exception as exc:  # pragma: no cover - best effort sandbox
        queue.put(("err", repr(exc)))


def _run_sync(handler: Callable[[Dict[str, Any]], Awaitable[Any]], params: Dict[str, Any], timeout: int, mem: int) -> Any:
    queue: mp.Queue = mp.Queue()
    proc = mp.Process(target=_target, args=(handler, params, queue, timeout, mem))
    proc.start()
    proc.join(timeout)
    if proc.is_alive():
        proc.terminate()
        proc.join()
        raise TimeoutError("Plugin execution timed out")
    if not queue.empty():
        status, payload = queue.get()
        if status == "ok":
            return payload
        raise RuntimeError(payload)
    if proc.exitcode and proc.exitcode != 0:
        raise RuntimeError(f"Plugin crashed with exit code {proc.exitcode}")
    raise RuntimeError("Plugin returned no result")


async def run_in_sandbox(
    handler: Callable[[Dict[str, Any]], Awaitable[Any]],
    params: Dict[str, Any],
    timeout: int = 10,
    memory_limit: int = 256 * 1024 * 1024,
) -> Any:
    """Execute ``handler`` in a subprocess with limits and timeout."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _run_sync, handler, params, timeout, memory_limit)

