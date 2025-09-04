"""
Lightweight TaskAnalyzer for query classification and capability mapping.

Classifies a user query into task types and required capabilities to
inform KIRE routing decisions and KHRP step selection.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TaskAnalysis:
    task_type: str
    required_capabilities: List[str] = field(default_factory=list)
    khrp_step_hint: Optional[str] = None
    hints: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.75


class TaskAnalyzer:
    """Pattern-based query classifier with provider capability mapping."""

    # Task keyword patterns (simple heuristic)
    _TASK_PATTERNS: Dict[str, List[str]] = {
        "code": ["code", "bug", "fix", "function", "class", "python", "typescript", "typescript", "compile", "refactor"],
        "reasoning": ["reason", "explain", "analyze", "logic", "why", "prove", "derive"],
        "summarization": ["summarize", "tl;dr", "brief", "condense", "summary"],
        "embedding": ["embed", "embedding", "semantic", "vector"],
        "lookup": ["search", "lookup", "find", "retrieve", "fetch"],
        "calc": ["calculate", "compute", "sum", "average", "mean", "median", "arithmetic"],
        "chat": ["chat", "talk", "discuss", "conversation", "help"],
    }

    # Capability mapping per task
    _TASK_CAPABILITIES: Dict[str, List[str]] = {
        "code": ["text", "code", "reasoning"],
        "reasoning": ["text", "reasoning"],
        "summarization": ["text"],
        "embedding": ["embeddings"],
        "lookup": ["text"],
        "calc": ["text", "reasoning"],
        "chat": ["text"],
    }

    # Provider capability hints
    _PROVIDER_CAPABILITIES: Dict[str, List[str]] = {
        "openai": ["text", "reasoning", "function_calling", "streaming"],
        "deepseek": ["text", "code", "reasoning"],
        "llamacpp": ["text"],
        "huggingface": ["text", "embeddings"],
        "gemini": ["text", "vision"],
    }

    def analyze(self, query: str, user_ctx: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> TaskAnalysis:
        q = (query or "").lower()

        # Determine task type by keywords (first match precedence)
        for task, keywords in self._TASK_PATTERNS.items():
            if any(k in q for k in keywords):
                caps = self._TASK_CAPABILITIES.get(task, ["text"])
                # Basic step hints
                step = None
                if task in ("reasoning", "calc"):
                    step = "reasoning_core"
                elif task == "summarization":
                    step = "output_rendering"
                elif task == "lookup":
                    step = "evidence_gathering"
                return TaskAnalysis(task_type=task, required_capabilities=caps, khrp_step_hint=step, hints={}, confidence=0.85)

        # Default to chat
        return TaskAnalysis(task_type="chat", required_capabilities=self._TASK_CAPABILITIES["chat"], khrp_step_hint=None, hints={}, confidence=0.6)

    def provider_supports(self, provider: str, required_caps: List[str]) -> bool:
        caps = self._PROVIDER_CAPABILITIES.get(provider.lower(), ["text"])  # assume at least text
        return all(c in caps for c in required_caps)

