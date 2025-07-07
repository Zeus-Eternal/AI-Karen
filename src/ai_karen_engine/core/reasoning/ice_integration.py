"""Integrated Cognitive Engine (ICE) wrapper.

This module exposes a lightweight approximation of the ICE reasoning
workflow. It uses the :class:`SoftReasoningEngine` for memory recall and a
local LLM helper to generate short analytical summaries. New information is
added to the memory store when it exceeds an entropy threshold.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

 
from integrations.llm_registry import registry as llm_registry

from integrations.llm_utils import LLMUtils

from ai_karen_engine.core.soft_reasoning_engine import SoftReasoningEngine


class KariICEWrapper:
    """Provide a simple ICE-style reasoning interface."""

    def __init__(self, threshold: float = 0.3, llm: LLMUtils | None = None) -> None:
        self.engine = SoftReasoningEngine()
        self.threshold = threshold
 
        if llm is not None:
            self.llm = llm
        else:
            self.llm = llm_registry.get_active() or LLMUtils()
 

    def process(self, text: str) -> Dict[str, Any]:
        """Return entropy, memory matches and a short analysis."""
        matches = self.engine.query(text, top_k=5)
        top_score = matches[0]["score"] if matches else 0.0
        entropy = 1.0 - top_score
        if entropy > self.threshold:
            self.engine.ingest(text)
        context = "\n".join(m["payload"]["text"] for m in matches)
        prompt = (
            "Summarize the user's request and highlight any new information\n"
            f"Memory:\n{context}\nRequest:{text}\nSummary:"
        )
        analysis = self.llm.generate_text(prompt, max_tokens=64)
        return {
            "entropy": entropy,
            "memory_matches": matches,
            "analysis": analysis.strip(),
        }

    async def aprocess(self, text: str) -> Dict[str, Any]:
        """Async wrapper around :meth:`process`."""
        return await asyncio.to_thread(self.process, text)
