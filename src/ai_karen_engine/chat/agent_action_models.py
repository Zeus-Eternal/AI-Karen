"""
Standardized agent action models for unified action handling across the system.

This module provides the core data models for agent actions, ensuring consistent
action representation across the orchestrator, extensions, tools, and monitoring systems.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import uuid

try:
    from pydantic import BaseModel, Field, ConfigDict
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field, ConfigDict


class AgentActionType(str, Enum):
    """Typed agent actions for consistent handling across the system."""

    ANSWER = "answer"
    SEARCH_WEB = "search_web"
    USE_EXTENSION = "use_extension"
    RETRIEVE_MEMORY = "retrieve_memory"
    EXECUTE_CODE = "execute_code"
    CALL_TOOL = "call_tool"
    ASK_FOLLOWUP = "ask_followup"
    DEFER_TO_FALLBACK = "defer_to_fallback"
    TERMINATE = "terminate"


class AgentAction(BaseModel):
    """Normalized agent action across all systems.

    This model provides a unified contract for agent decisions, ensuring that
    the orchestrator, extensions, tools, and monitoring all use the same
    action representation.
    """

    action: AgentActionType
    reason: str
    tool: Optional[str] = None  # tool_name or extension_id
    extension_id: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtensionExecutionResult(BaseModel):
    """Standardized extension execution result.

    Provides a consistent structure for extension outputs that can be
    consumed by the context integrator and other systems.
    """

    extension_id: str
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WebSearchResult(BaseModel):
    """Standardized web search result with citations.

    Wraps search results from InternetCapabilityService in a format
    compatible with the agent action system.
    """

    query: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentTrace(BaseModel):
    """Trace of agent execution for debugging and monitoring.

    Records the sequence of actions taken by the agent during a run,
    providing observability and the ability to replay or analyze behavior.
    """

    correlation_id: str
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    total_steps: int = 0
    status: str = "in_progress"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    """Standardized citation model.

    Represents a single citation from a web search or other source,
    with all necessary metadata for display and tracking.
    """

    id: str
    url: str
    title: str
    snippet: str
    index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolExecutionResult(BaseModel):
    """Result from tool execution."""

    tool_name: str = Field(description="Name of the tool executed")
    success: bool = Field(description="Whether execution succeeded")
    result: Optional[Any] = Field(default=None, description="Tool output")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time_ms: int = Field(
        default=0, description="Execution time in milliseconds"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


@dataclass
class AgentStep:
    """Single step in agent execution."""

    step_id: str
    action_type: AgentActionType
    action: AgentAction
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[
        Union[ToolExecutionResult, ExtensionExecutionResult, WebSearchResult]
    ] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentExecutionTrace:
    """Complete trace of agent execution."""

    correlation_id: str
    conversation_id: str
    user_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    steps: List[AgentStep] = field(default_factory=list)
    final_answer: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "in_progress"

    def add_step(self, step: AgentStep) -> None:
        """Add a step to the trace."""
        self.steps.append(step)

    def complete(self, final_answer: str) -> None:
        """Mark execution as completed."""
        self.final_answer = final_answer
        self.completed_at = datetime.utcnow()
        self.status = "completed"

    def fail(self, error: str) -> None:
        """Mark execution as failed."""
        self.completed_at = datetime.utcnow()
        self.status = "failed"
        self.metadata["error"] = error

    def timeout(self) -> None:
        """Mark execution as timed out."""
        self.completed_at = datetime.utcnow()
        self.status = "timeout"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "correlation_id": self.correlation_id,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "steps": [
                {
                    "step_id": step.step_id,
                    "action_type": step.action_type.value
                    if isinstance(step.action_type, AgentActionType)
                    else step.action_type,
                    "action": step.action.model_dump() if step.action else None,
                    "started_at": step.started_at.isoformat()
                    if step.started_at
                    else None,
                    "completed_at": step.completed_at.isoformat()
                    if step.completed_at
                    else None,
                    "error": step.error,
                    "metadata": step.metadata,
                }
                for step in self.steps
            ],
            "final_answer": self.final_answer,
            "metadata": self.metadata,
            "status": self.status,
        }


class AgentConfig(BaseModel):
    """Configuration for agent execution."""

    model_config = ConfigDict(use_enum_values=True)

    max_steps: int = Field(default=5, ge=1, le=20, description="Maximum agent steps")
    max_tool_invocations: int = Field(
        default=10, ge=1, le=50, description="Maximum tool invocations"
    )
    max_web_searches: int = Field(
        default=3, ge=1, le=10, description="Maximum web searches"
    )
    max_extensions_per_run: int = Field(
        default=5, ge=1, le=20, description="Maximum extensions per run"
    )
    timeout_seconds: int = Field(
        default=300, ge=10, le=600, description="Agent timeout in seconds"
    )
    tool_timeout_seconds: int = Field(
        default=30, ge=5, le=120, description="Tool timeout in seconds"
    )
    web_search_timeout_seconds: int = Field(
        default=60, ge=10, le=300, description="Web search timeout in seconds"
    )
    extension_timeout_seconds: int = Field(
        default=30, ge=5, le=120, description="Extension timeout in seconds"
    )
    citation_min_confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Minimum confidence for citations"
    )
    search_result_max_urls: int = Field(
        default=5, ge=1, le=20, description="Maximum URLs per search"
    )
    crawl_max_depth: int = Field(
        default=1, ge=1, le=3, description="Maximum crawl depth"
    )
    enable_agent_mode: bool = Field(default=True, description="Enable agent mode")
    degraded_mode_threshold: int = Field(
        default=3, ge=1, le=10, description="Provider failures before degraded mode"
    )
