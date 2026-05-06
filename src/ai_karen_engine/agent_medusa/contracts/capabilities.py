from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

class AgentCapabilityType(str, Enum):
    """Types of agent capabilities"""
    REASONING = "reasoning"
    RESEARCH = "research"
    PLANNING = "planning"
    CODING = "coding"
    IMAGE_GENERATION = "image_generation"
    DATA_ANALYSIS = "data_analysis"
    WEB_BROWSING = "web_browsing"
    TOOL_USE = "tool_use"
    MEMORY_ACCESS = "memory_access"

@dataclass
class AgentCapability:
    """Represents a specific capability of an agent"""
    type: AgentCapabilityType
    name: str
    description: str
    level: int = 1  # 1-5
    metadata: Dict[str, Any] = field(default_factory=dict)
