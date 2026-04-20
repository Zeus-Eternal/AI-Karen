from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from datetime import datetime
from enum import Enum

class ResponseStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    ERROR = "error"
    TIMEOUT = "timeout"
    DEGRADED = "degraded"

@dataclass
class MedusaRuntimeResponse:
    """Standard response from the AgentMedusa runtime"""
    request_id: str
    status: ResponseStatus
    content: str
    intermediate_steps: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    execution_time_ms: float = 0.0
    
    # Trace of which agents were involved
    agent_trace: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "status": self.status.value,
            "content": self.content,
            "intermediate_steps": self.intermediate_steps,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "execution_time_ms": self.execution_time_ms,
            "agent_trace": self.agent_trace
        }
