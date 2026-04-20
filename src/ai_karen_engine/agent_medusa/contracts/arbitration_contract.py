from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

class ArbitrationReason(str, Enum):
    CONFLICTING_RESULTS = "conflicting_results"
    UNCERTAINTY = "uncertainty"
    MULTIPLE_PATHS = "multiple_paths"
    QUALITY_CHECK = "quality_check"
    RESOURCE_CONSTRAINTS = "resource_constraints"

@dataclass
class ArbitrationRequest:
    """Request for the Medusa Arbitrator to resolve a situation"""
    reason: ArbitrationReason
    context: Dict[str, Any]
    options: List[Dict[str, Any]] = field(default_factory=list)
    request_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "reason": self.reason.value,
            "context": self.context,
            "options": self.options,
            "request_id": self.request_id
        }

@dataclass
class ArbitrationDecision:
    """The outcome of an arbitration process"""
    chosen_option_id: str
    rationale: str
    adjustments: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chosen_option_id": self.chosen_option_id,
            "rationale": self.rationale,
            "adjustments": self.adjustments
        }
