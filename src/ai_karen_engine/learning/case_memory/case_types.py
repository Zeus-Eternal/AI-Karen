from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

@dataclass(frozen=True)
class ToolIO:
    """Tool input/output capture for case memory"""
    tool_name: str
    args: Dict[str, Any]
    output: Any
    started_at: datetime
    ended_at: datetime
    status: str  # "ok" | "error"

@dataclass(frozen=True)
class StepTrace:
    """Single step execution trace"""
    thought: str
    action: Optional[str]
    tool_io: Optional[ToolIO]

@dataclass(frozen=True)
class Reward:
    """Reward signal for case quality assessment"""
    score: float
    signals: Dict[str, float]

@dataclass(frozen=True)
class Case:
    """Complete case memory record"""
    case_id: str
    tenant_id: str
    user_id: Optional[str]
    created_at: datetime
    task_text: str
    goal_text: Optional[str]
    plan_text: Optional[str]
    steps: Tuple[StepTrace, ...]
    outcome_text: str
    tags: Tuple[str, ...]
    reward: Reward
    pointers: Dict[str, str]
    embeddings: Dict[str, List[float]]  # {"task":[...], "plan":[...], "outcome":[...]}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
