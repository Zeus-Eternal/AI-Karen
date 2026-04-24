"""Generic OpenAI-compatible provider alias.

This keeps adapter code neutral: any OpenAI-style endpoint can be configured
through the same runtime without introducing engine-specific provider classes.
"""

from __future__ import annotations

from ai_karen_engine.integrations.providers.openai_provider import OpenAIProvider


class OpenAICompatibleProvider(OpenAIProvider):
    """Alias for OpenAI-compatible endpoints."""

    def __init__(self, *args, **kwargs):
        provider_name = kwargs.pop("provider_name", None) or "openai_compatible"
        super().__init__(*args, provider_name=provider_name, **kwargs)

