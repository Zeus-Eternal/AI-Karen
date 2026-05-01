from __future__ import annotations

from .contracts import GuardOutcome, MemoryCandidate, MemoryGuardDecision


def evaluate_guardrails(candidate: MemoryCandidate) -> MemoryGuardDecision:
    reasons = []
    risk = float(candidate.metadata.get("risk_score", 0.0))
    if candidate.metadata.get("tenant_mismatch"):
        return MemoryGuardDecision(GuardOutcome.REJECT, ["cross_tenant_contamination"], 1.0, True)
    if candidate.source in {"web", "plugin"} and float(candidate.metadata.get("source_trust", 0.0)) < 0.8:
        reasons.append("untrusted_tool_or_web_source")
        return MemoryGuardDecision(GuardOutcome.QUARANTINE, reasons, max(risk, 0.8), True)
    if "ignore prior instructions" in candidate.text.lower():
        return MemoryGuardDecision(GuardOutcome.REJECT, ["prompt_in_memory_attack"], 1.0, True)
    if risk >= 0.8:
        return MemoryGuardDecision(GuardOutcome.REQUIRES_REVIEW, ["high_risk_memory"], risk, True)
    return MemoryGuardDecision(GuardOutcome.ALLOW, reasons, risk, False)
