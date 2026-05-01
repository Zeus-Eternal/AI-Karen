from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MemoryClass(str, Enum):
    STM = "stm"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    LESSON = "lesson"
    QUARANTINE = "quarantine"


class MemoryActivationMode(str, Enum):
    NONE = "none"
    FAST = "fast"
    PROFILE = "profile"
    PROCEDURAL = "procedural"
    GRAPH = "graph"
    DEEP = "deep"


class GuardOutcome(str, Enum):
    ALLOW = "allow"
    QUARANTINE = "quarantine"
    REJECT = "reject"
    REQUIRES_REVIEW = "requires_review"


@dataclass(slots=True)
class MemoryActivationDecision:
    mode: MemoryActivationMode = MemoryActivationMode.FAST
    reasons: List[str] = field(default_factory=list)
    max_latency_ms: int = 250
    top_k: int = 8
    include_profile: bool = False
    include_procedural: bool = False
    include_graph: bool = False
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass(slots=True)
class ProcedureArtifact:
    id: str
    name: str
    trigger_patterns: List[str]
    tool_sequence: List[str]
    success_count: int = 0
    failure_count: int = 0
    confidence: float = 0.0
    tenant_scope: str = "tenant"
    permissions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class LessonArtifact:
    id: str
    lesson_type: str
    failure_signature: str
    correction: str
    applies_to: List[str] = field(default_factory=list)
    severity: str = "medium"
    confidence: float = 0.0
    quarantine_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ConsolidationDecision:
    promote: bool
    source_class: MemoryClass
    target_class: MemoryClass
    reason: str
    confidence: float
    requires_review: bool = False


@dataclass(slots=True)
class MemoryGuardDecision:
    outcome: GuardOutcome
    reasons: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    required_review: bool = False


@dataclass(slots=True)
class MemoryCandidate:
    id: str
    text: str
    memory_class: MemoryClass
    source: str
    tenant_id: str
    user_id: str
    confidence: float = 0.0
    importance: float = 0.0
    freshness: float = 1.0
    provenance: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
