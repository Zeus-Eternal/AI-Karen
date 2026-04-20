from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

class PermissionScope(str, Enum):
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    FULL_ACCESS = "full_access"
    SENSITIVE = "sensitive"
    NO_ACCESS = "no_access"

@dataclass
class MedusaRuntimePolicy:
    """Policy constraints for the AgentMedusa runtime session"""
    max_steps_total: int = 50
    max_concurrent_agents: int = 5
    max_tokens_per_session: int = 100000
    
    # Permission mappings for agents
    agent_permissions: Dict[str, PermissionScope] = field(default_factory=dict)
    
    # Global flags
    allow_external_calls: bool = True
    require_arbitration_on_conflict: bool = True
    enforce_sandbox: bool = True
    
    def get_agent_scope(self, agent_id: str) -> PermissionScope:
        return self.agent_permissions.get(agent_id, PermissionScope.READ_ONLY)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_steps_total": self.max_steps_total,
            "max_concurrent_agents": self.max_concurrent_agents,
            "max_tokens_per_session": self.max_tokens_per_session,
            "agent_permissions": {k: v.value for k, v in self.agent_permissions.items()},
            "allow_external_calls": self.allow_external_calls,
            "require_arbitration_on_conflict": self.require_arbitration_on_conflict,
            "enforce_sandbox": self.enforce_sandbox
        }
