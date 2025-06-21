"""Placeholder for live capsule monitoring UI."""

from __future__ import annotations

import json
from .. import tauri


def render(events: list[dict]) -> str:
    """Return a JSON string for now."""
    return json.dumps(events, indent=2)
