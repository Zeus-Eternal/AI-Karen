"""Jinja2-based prompt construction utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


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
        return template.render(**data)
