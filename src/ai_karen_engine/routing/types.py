"""
KIRE routing types - concrete types used throughout the routing system.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RouteRequest:
    """Request for LLM routing."""
    user_id: str
    task_type: str  # "chat"|"code"|"reasoning"|"summarization"
    query: str = ""
    khrp_step: Optional[str] = None  # "intent_capture"|"reasoning_core"|...
    context: Dict[str, Any] = field(default_factory=dict)
    requirements: Dict[str, Any] = field(default_factory=dict)  # capabilities, latency, cost, locality


@dataclass
class RouteDecision:
    """LLM routing decision."""
    provider: str
    model: str
    reasoning: str
    confidence: float
    fallback_chain: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelAssignment:
    """Model assignment for a task type."""
    task_type: str
    provider: str
    model: str
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserProfile:
    """User's LLM profile configuration."""
    profile_id: str
    name: str
    assignments: Dict[str, ModelAssignment]
    fallback_chain: List[str]
    khrp_config: Dict[str, Any] = field(default_factory=dict)