from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

class AgentCapability(str, Enum):
    WEB_SEARCH = "web_search"
    CODE_INTERPRETER = "code_interpreter"
    FILE_OPERATIONS = "file_operations"
    DATABASE_ACCESS = "database_access"
    EXTENSION_PLATFORM = "extension_platform"
    REASONING = "reasoning"
    MEMORY_RETRIEVAL = "memory_retrieval"

@dataclass
class SubagentContract:
    """Contract that every specialist agent must fulfill"""
    agent_id: str
    role: str
    capabilities: List[AgentCapability] = field(default_factory=list)
    system_prompt_template: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    
    def validate_action(self, action_type: str) -> bool:
        """Checks if the agent is allowed to perform a certain action"""
        # Placeholder for more complex validation logic
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "capabilities": [cap.value for cap in self.capabilities],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
