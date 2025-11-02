from typing import Any, Dict, Optional

from plugin_marketplace.memory_manager import MemoryManager

memory = MemoryManager()


async def run(_params: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> str:
    """Return a friendly greeting and store it in memory."""
    result = "Hey there! I'm Kari—your AI co-pilot. What can I help with today?"
    memory.write(user_context or {}, "greet", result)
    return result
