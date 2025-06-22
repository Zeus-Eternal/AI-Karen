"""Simple chart viewer stub."""

from typing import Iterable


def show_chart(data: Iterable[float]) -> str:
    """Return a textual representation of a chart."""
    points = ", ".join(str(x) for x in data)
    return f"chart: [{points}]"
