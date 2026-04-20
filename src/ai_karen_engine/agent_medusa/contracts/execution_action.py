from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from enum import Enum

class ActionType(str, Enum):
    TOOL_CALL = "tool_call"
    EXTENSION_DISPATCH = "extension_dispatch"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    INTERNAL_THOUGHT = "internal_thought"
    COMMUNICATION = "communication"
    FINAL_ANSWER = "final_answer"

@dataclass
class ExecutionAction:
    """A specific action taken by an agent during execution"""
    action_type: ActionType
    agent_id: str
    step_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type.value,
            "agent_id": self.agent_id,
            "step_id": self.step_id,
            "payload": self.payload,
            "metadata": self.metadata
        }
