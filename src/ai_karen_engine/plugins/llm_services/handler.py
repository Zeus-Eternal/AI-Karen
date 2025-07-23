"""Base handler for llm_services plugin.

This plugin acts as a stub for loading LLM service sub-plugins.
"""

async def run(params: dict) -> str:
    """Return a simple acknowledgement that the service plugin is loaded."""
    return "ok"
