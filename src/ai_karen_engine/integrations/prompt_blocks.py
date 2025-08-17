"""Helpers to render provider information blocks for prompts."""

from __future__ import annotations

from typing import Any, Dict


def render_providers_block(statuses: Dict[str, Any]) -> str:
    """Return a bullet list of provider statuses."""

    lines = []
    for name, data in statuses.items():
        health = "healthy" if data.get("healthy") else "unhealthy"
        latency = data.get("latency_ms", "?")
        models = ", ".join(data.get("models", [])) or "n/a"
        lines.append(f"- {name}: {health} ({latency}ms) models: {models}")
    return "\n".join(lines)


def render_providers_table(statuses: Dict[str, Any]) -> str:
    """Return a Markdown table of provider statuses."""

    header = "| Provider | Healthy | Latency (ms) | Models |\n|---|---|---|---|"
    rows = []
    for name, data in statuses.items():
        health = "✅" if data.get("healthy") else "❌"
        latency = str(data.get("latency_ms", "?"))
        models = ", ".join(data.get("models", [])) or "n/a"
        rows.append(f"| {name} | {health} | {latency} | {models} |")
    return "\n".join([header, *rows])


__all__ = ["render_providers_block", "render_providers_table"]

