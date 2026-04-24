"""Neutral local GGUF runtime alias."""

from __future__ import annotations

from .transformers_runtime import TransformersRuntime

LocalGGUFRuntime = TransformersRuntime

__all__ = ["LocalGGUFRuntime"]
