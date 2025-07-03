"""Inline form builder stub."""

from typing import Dict, Iterable


def render_form(fields: Iterable[str]) -> Dict[str, str | None]:
    """Return a dictionary with None values for the given field names."""
    return {field: None for field in fields}
