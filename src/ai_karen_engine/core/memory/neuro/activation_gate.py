from __future__ import annotations

from .contracts import MemoryActivationDecision, MemoryActivationMode
from .settings import get_neuro_settings


def decide_activation_mode(*, query: str, latency_budget_ms: int = 250, has_profile: bool = False) -> MemoryActivationDecision:
    settings = get_neuro_settings()
    q = (query or "").lower()
    decision = MemoryActivationDecision(max_latency_ms=min(latency_budget_ms, settings.fast_recall_timeout_ms))
    if any(x in q for x in ["joke", "hello"]):
        decision.mode = MemoryActivationMode.NONE
    elif any(x in q for x in ["favorite", "my preference", "my birthday"]):
        decision.mode = MemoryActivationMode.PROFILE
        decision.include_profile = has_profile
    elif any(x in q for x in ["same workflow", "search the internet", "tool"]):
        decision.mode = MemoryActivationMode.PROCEDURAL
        decision.include_procedural = settings.procedural_enabled
    elif any(x in q for x in ["why did we", "relation", "linked"]):
        decision.mode = MemoryActivationMode.GRAPH
        decision.include_graph = settings.graph_escalation_enabled
    else:
        decision.mode = MemoryActivationMode.FAST
    decision.reasons.append(f"selected_mode:{decision.mode.value}")
    return decision
