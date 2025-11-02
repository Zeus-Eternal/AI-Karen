from pathlib import Path
from typing import Any, Dict, Optional

try:  # optional dependency
    from jinja2 import Template
except Exception:  # pragma: no cover - optional dep
    Template = None  # type: ignore

from plugin_marketplace.memory_manager import MemoryManager

memory = MemoryManager()


async def run(params: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> str:
    """Return a friendly greeting rendered from ``prompt.txt`` and store it."""
    prompt_file = Path(__file__).with_name("prompt.txt")
    data = prompt_file.read_text(encoding="utf-8")
    if Template is None:
        result = data.strip()
    else:
        result = Template(data).render(**params)

    memory.write(user_context or {}, "greet", result)
    return result
