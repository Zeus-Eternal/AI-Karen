from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from .events import AgentEvent

@dataclass
class AgentTrace:
    """Represents a full execution trace of an agent"""
    trace_id: str
    agent_id: str
    events: List[AgentEvent] = field(default_factory=list)
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_ms(self) -> Optional[float]:
        if not self.end_time:
            return None
        return (self.end_time - self.start_time).total_seconds() * 1000.0

    def add_event(self, event: AgentEvent) -> None:
        self.events.append(event)
        
    def complete(self) -> None:
        self.end_time = datetime.now(timezone.utc)
