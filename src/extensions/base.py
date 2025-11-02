"""Compatibility layer for legacy BaseExtension imports.

This module re-exports :class:`BaseExtension` from the production
``ai_karen_engine.extensions`` package so that historical imports using
``src.extensions.base`` resolve to the fully featured engine
implementation.
"""

from ai_karen_engine.extensions.base import BaseExtension

__all__ = ["BaseExtension"]
