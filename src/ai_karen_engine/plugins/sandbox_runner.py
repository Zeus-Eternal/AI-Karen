import asyncio
import importlib
import json
import os
import resource
import sys


def _set_limits(cpu_seconds: int) -> None:
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
    except Exception:
        pass


async def _run(module_name: str, params: dict) -> None:
    mod = importlib.import_module(module_name)
    run = getattr(mod, "run")
    if asyncio.iscoroutinefunction(run):
        result = await run(params)
    else:
        result = run(params)
    print(json.dumps(result))


def main() -> None:
    module = sys.argv[1]
    cpu = int(os.environ.get("KARI_CPU_LIMIT", "2"))
    _set_limits(cpu)
    os.environ.clear()
    params = json.load(sys.stdin)
    asyncio.run(_run(module, params))


if __name__ == "__main__":
    main()
