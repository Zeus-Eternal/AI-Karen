"""Simplified ICE integration wrapper for Kari AI.

This module emulates the Integrated Cognitive Engine (ICE) using the
existing SoftReasoningEngine. It computes a basic entropy score based on
similarity and stores surprising text into memory.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..soft_reasoning_engine import SoftReasoningEngine


class KariICEWrapper:
    """Wrapper providing ICE-like reasoning with memory recall."""

    def __init__(self, threshold: float = 0.3) -> None:
        self.engine = SoftReasoningEngine()
        self.threshold = threshold

    def process(self, text: str) -> Dict[str, Any]:
        """Process text and return entropy and memory matches."""
        matches = self.engine.query(text, top_k=5)
        top_score = matches[0]["score"] if matches else 0.0
        entropy = 1.0 - top_score
        if entropy > self.threshold:
            self.engine.ingest(text)
        return {"entropy": entropy, "memory_matches": matches}
