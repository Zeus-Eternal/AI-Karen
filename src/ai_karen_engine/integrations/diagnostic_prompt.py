"""Compose admin diagnostic prompts using provider data."""

from __future__ import annotations

from typing import Any, Dict

from .prompt_blocks import render_providers_block, render_providers_table


def make_admin_diagnostic_prompt(
    statuses: Dict[str, Any], use_table: bool = False
) -> str:
    """Create a diagnostic prompt embedding provider information."""

    renderer = render_providers_table if use_table else render_providers_block
    providers_section = renderer(statuses)
    return (
        "System diagnostics report:\n\n"
        "Providers:\n"
        f"{providers_section}\n"
    )


__all__ = ["make_admin_diagnostic_prompt"]

