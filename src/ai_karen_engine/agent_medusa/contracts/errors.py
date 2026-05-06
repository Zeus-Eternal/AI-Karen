from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from enum import Enum

class AgentErrorCode(str, Enum):
    """Enumeration of agent system error codes"""
    INVALID_REQUEST = "invalid_request"
    AUTH_FAILED = "auth_failed"
    PERMISSION_DENIED = "permission_denied"
    RESOURCE_NOT_FOUND = "resource_not_found"
    EXECUTION_FAILED = "execution_failed"
    TIMEOUT = "timeout"
    SAFETY_VIOLATION = "safety_violation"
    QUARANTINED = "quarantined"
    NETWORK_ERROR = "network_error"
    INTERNAL_ERROR = "internal_error"
    DEPENDENCY_ERROR = "dependency_error"
    VALIDATION_ERROR = "validation_error"

@dataclass
class AgentError:
    """Represents an error in the agent system"""
    code: AgentErrorCode
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    recoverable: bool = True
    correlation_id: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)
