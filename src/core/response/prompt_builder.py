"""Jinja2-based prompt construction utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence, cast

from jinja2 import Environment, FileSystemLoader


class PromptBuilder:
    """Load and render Jinja2 templates for prompts."""

    def __init__(self, template_dir: Path | str) -> None:
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, **data: Any) -> str:
        """Render ``template_name`` with the provided ``data``."""

        template = self.env.get_template(f"{template_name}.j2")
        return cast(str, template.render(**data))

    # -- Convenience wrappers -------------------------------------------------

    def system_base(self, persona: str) -> str:
        """Render the ``system_base`` template with *persona*."""

        return self.render("system_base", persona=persona)

    def user_frame(self, user_input: str) -> str:
        """Render the ``user_frame`` template with *user_input*."""

        return self.render("user_frame", user_input=user_input)

    def onboarding(self, gaps: Sequence[str]) -> str:
        """Render the ``onboarding`` template with profile *gaps*."""

        return self.render("onboarding", gaps=gaps)

    def build(
        self,
        *,
        persona: str,
        user_input: str,
        context: Sequence[str] | None = None,
        profile_gaps: Sequence[str] | None = None,
        system_prompts: Sequence[str] | None = None,
        max_history: int | None = None,
    ) -> str:
        """Assemble a full prompt from the provided pieces."""

        parts = [self.system_base(persona)]
        if context:
            history = list(context)
            if max_history is not None:
                history = history[-max_history:]
            parts.extend(self.user_frame(msg) for msg in history)
        parts.append(self.user_frame(user_input))
        if profile_gaps:
            parts.append(self.onboarding(profile_gaps))
        all_parts = list(system_prompts or []) + parts
        return "\n".join(all_parts)
