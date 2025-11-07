from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, runtime_checkable, List


@runtime_checkable
class SynthesisSubEngine(Protocol):
    """Optional sub-engine to run inside ICE's synthesis step.
    Examples: LangGraph, Haystack, DSPy orchestrations.
    """
    def run(self, *, text: str, context: str, mode: str, max_tokens: int) -> str:
        ...


class LangGraphSubEngine(SynthesisSubEngine):
    """Minimal example to show how to plug a LangGraph-like orchestrator."""
    def __init__(self, graph: Any) -> None:
        self.graph = graph

    def run(self, *, text: str, context: str, mode: str, max_tokens: int) -> str:
        try:
            # Graph should accept an input dict and return a string/summary
            res = self.graph.run({"text": text, "context": context, "mode": mode, "max_tokens": max_tokens})
            if isinstance(res, str):
                return res
            return str(res)
        except Exception:
            # Fallback silently; ICE will handle graceful degradation
            return ""


class DSPySubEngine(SynthesisSubEngine):
    """Placeholder for DSPy pipeline; optimized prompts go here."""
    def __init__(self, pipeline: Any) -> None:
        self.pipeline = pipeline

    def run(self, *, text: str, context: str, mode: str, max_tokens: int) -> str:
        try:
            return self.pipeline(text=text, context=context, mode=mode, max_tokens=max_tokens)
        except Exception:
            return ""
