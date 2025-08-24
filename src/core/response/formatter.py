"""DRY formatter with optional CopilotKit integration."""
from __future__ import annotations

from typing import Any

try:  # pragma: no cover - optional dependency
    from copilotkit import enhance_text  # type: ignore
except Exception:  # pragma: no cover
    enhance_text = None  # type: ignore


class DRYFormatter:
    """Format responses consistently with optional CopilotKit hooks."""

    def __init__(self, enable_copilotkit: bool = True) -> None:
        self.enable_copilotkit = enable_copilotkit and enhance_text is not None

    def format(self, text: str, **_: Any) -> str:
        """Return formatted text with graceful degradation."""

        result = f"## Response\n\n{text.strip()}"
        if self.enable_copilotkit and enhance_text is not None:
            try:
                result = enhance_text(result)
            except Exception:
                pass
        return result
