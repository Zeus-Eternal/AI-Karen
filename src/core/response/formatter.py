"""DRY formatter with optional CopilotKit integration.

The formatter provides a small set of helpers for building responses with a
consistent structure.  It intentionally keeps the logic lightweight and free of
heavy dependencies so that it can be reused across the code base.  If the
optional :mod:`copilotkit` package is available the final formatted text can be
"enhanced" before being returned.  When the dependency is missing the formatter
degrades gracefully and simply returns the unmodified result.
"""

from __future__ import annotations

from typing import Iterable, Optional

try:  # pragma: no cover - optional dependency
    from copilotkit import enhance_text
except Exception:  # pragma: no cover
    enhance_text = None


class DRYFormatter:
    """Format responses consistently with optional CopilotKit hooks."""

    def __init__(self, enable_copilotkit: bool = True) -> None:
        self.enable_copilotkit = bool(enable_copilotkit and enhance_text is not None)

    # -- basic building blocks -------------------------------------------------
    @staticmethod
    def heading(text: str, level: int = 2) -> str:
        """Return a Markdown heading."""

        return f"{'#' * level} {text.strip()}"

    @staticmethod
    def bullet_list(items: Iterable[str]) -> str:
        """Return a Markdown bullet list."""

        return "\n".join(f"- {item.strip()}" for item in items)

    @staticmethod
    def code_block(code: str, language: str = "") -> str:
        """Return a fenced code block."""

        lang = f"{language}\n" if language else ""
        return f"```{lang}{code.strip()}\n```"

    # -- public API ------------------------------------------------------------
    def format(
        self,
        heading: str,
        body: str,
        bullets: Optional[Iterable[str]] = None,
        code: Optional[str] = None,
        language: str = "",
    ) -> str:
        """Build a response with optional bullets and code block.

        Parameters
        ----------
        heading:
            Heading text for the response.
        body:
            Main body text.
        bullets:
            Optional iterable of bullet point strings.
        code:
            Optional code snippet to include.
        language:
            Optional language indicator for the code block.
        """

        parts = [self.heading(heading), "", body.strip()]

        if bullets:
            parts.extend(["", self.bullet_list(bullets)])

        if code:
            parts.extend(["", self.code_block(code, language)])

        result = "\n".join(parts).strip()

        if self.enable_copilotkit and enhance_text is not None:
            try:  # pragma: no cover - defensive
                result = enhance_text(result)
            except Exception:  # pragma: no cover - degrade gracefully
                pass

        return result

