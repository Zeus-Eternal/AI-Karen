from dataclasses import dataclass, field
from typing import Any

@dataclass(slots=True)
class ResponseTask:
    task_id: str
    messages: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)
