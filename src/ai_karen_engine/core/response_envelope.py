"""Utilities for building structured response envelopes."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def build_response_envelope(
    final_text: str,
    provider: str,
    model: str,
    metadata: Optional[Dict[str, Any]] = None,
    suggestions: Optional[List[str]] = None,
    alerts: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Create a standardized response envelope with no extraneous text."""
    meta = metadata.copy() if metadata else {}
    meta.setdefault("provider", provider)
    meta.setdefault("model", model)
    return {
        "final": final_text,
        "meta": meta,
        "suggestions": suggestions or [],
        "alerts": alerts or [],
    }
