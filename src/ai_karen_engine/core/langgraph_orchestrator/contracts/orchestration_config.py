from dataclasses import dataclass

@dataclass
class LangGraphOrchestrationConfig:
    """Configuration for the orchestration system"""

    enable_auth_gate: bool = True
    enable_safety_gate: bool = True
    enable_memory_fetch: bool = True
    enable_approval_gate: bool = False
    streaming_enabled: bool = False
    checkpoint_enabled: bool = True
    max_retries: int = 3
    timeout_seconds: int = 300
