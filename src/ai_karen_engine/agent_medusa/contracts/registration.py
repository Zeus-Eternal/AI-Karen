from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from .capabilities import AgentCapability

@dataclass
class AgentRegistration:
    """Represents a registered agent in the Medusa system"""
    agent_id: str
    name: str
    description: str
    capabilities: List[AgentCapability] = field(default_factory=list)
    version: str = "1.0.0"
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "active"  # active, inactive, maintenance
    metadata: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
