import asyncio
from ai_karen_engine.plugins.tui_fallback import tui

async def run(params: dict) -> dict:
    """Launch the interactive TUI with the given state dictionaries."""
    plugin_states = params.get("plugin_states", {})
    system_metrics = params.get("system_metrics", {})
    await tui.start_tui(plugin_states, system_metrics)
    return {"status": "TUI closed gracefully"}
