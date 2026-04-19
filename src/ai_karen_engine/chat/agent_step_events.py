"""
Agent step event models for streaming real-time agent execution state.

This module defines the event types that are emitted during agent execution
and sent to the frontend via the streaming infrastructure.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from pydantic import BaseModel, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field


class AgentStepEventType(str, Enum):
    """Agent step event types for streaming."""

    AGENT_STEP_STARTED = "agent_step_started"
    AGENT_STEP_COMPLETED = "agent_step_completed"
    TOOL_EXECUTION_STARTED = "tool_execution_started"
    TOOL_EXECUTION_COMPLETED = "tool_execution_completed"
    WEB_SEARCH_STARTED = "web_search_started"
    WEB_SEARCH_SOURCES_FOUND = "web_search_sources_found"
    EXTENSION_EXECUTION_STARTED = "extension_execution_started"
    EXTENSION_EXECUTION_COMPLETED = "extension_execution_completed"
    CITATION_BUNDLE_READY = "citation_bundle_ready"
    DEGRADED_MODE_ENTERED = "degraded_mode_entered"


class AgentStepEvent(BaseModel):
    """Base agent step event for streaming.

    All agent execution events extend this base model, providing
    consistent structure for frontend consumption.
    """

    type: AgentStepEventType
    step_id: str
    action_type: Optional[str] = None
    correlation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentStepStartedEvent(AgentStepEvent):
    """Emitted when an agent step begins."""

    step_count: int = 0
    max_steps: int = 0
    reason: Optional[str] = None
    tool: Optional[str] = None
    confidence: float = 1.0


class AgentStepCompletedEvent(AgentStepEvent):
    """Emitted when an agent step completes."""

    success: bool = True
    response_length: int = 0
    execution_time_ms: int = 0


class ToolExecutionStartedEvent(AgentStepEvent):
    """Emitted when a tool execution begins."""

    tool_name: str
    tool_type: Optional[str] = None


class ToolExecutionCompletedEvent(AgentStepEvent):
    """Emitted when a tool execution completes."""

    tool_name: str
    success: bool = True
    execution_time_ms: int = 0
    result_summary: Optional[str] = None


class WebSearchStartedEvent(AgentStepEvent):
    """Emitted when a web search begins."""

    query: str
    search_mode: Optional[str] = None


class WebSearchSourcesFoundEvent(AgentStepEvent):
    """Emitted when web search sources are found."""

    sources_count: int = 0
    query: Optional[str] = None
    execution_time_ms: int = 0


class ExtensionExecutionStartedEvent(AgentStepEvent):
    """Emitted when an extension execution begins."""

    extension_id: str
    extension_name: Optional[str] = None


class ExtensionExecutionCompletedEvent(AgentStepEvent):
    """Emitted when an extension execution completes."""

    extension_id: str
    success: bool = True
    execution_time_ms: int = 0
    result_summary: Optional[str] = None


class CitationBundleReadyEvent(AgentStepEvent):
    """Emitted when citations are ready for display."""

    citations: List[Dict[str, Any]] = Field(default_factory=list)
    sources_count: int = 0


class DegradedModeEnteredEvent(AgentStepEvent):
    """Emitted when the system enters degraded mode."""

    reason: str
    fallback_path: Optional[str] = None
    degraded_mode_type: Optional[str] = None


def create_agent_step_event(
    event_type: AgentStepEventType, step_id: str, **kwargs
) -> AgentStepEvent:
    """Factory function to create the appropriate agent step event.

    Args:
        event_type: The type of event to create
        step_id: Unique identifier for the step
        **kwargs: Additional fields specific to the event type

    Returns:
        An AgentStepEvent instance of the appropriate subtype
    """
    event_classes = {
        AgentStepEventType.AGENT_STEP_STARTED: AgentStepStartedEvent,
        AgentStepEventType.AGENT_STEP_COMPLETED: AgentStepCompletedEvent,
        AgentStepEventType.TOOL_EXECUTION_STARTED: ToolExecutionStartedEvent,
        AgentStepEventType.TOOL_EXECUTION_COMPLETED: ToolExecutionCompletedEvent,
        AgentStepEventType.WEB_SEARCH_STARTED: WebSearchStartedEvent,
        AgentStepEventType.WEB_SEARCH_SOURCES_FOUND: WebSearchSourcesFoundEvent,
        AgentStepEventType.EXTENSION_EXECUTION_STARTED: ExtensionExecutionStartedEvent,
        AgentStepEventType.EXTENSION_EXECUTION_COMPLETED: ExtensionExecutionCompletedEvent,
        AgentStepEventType.CITATION_BUNDLE_READY: CitationBundleReadyEvent,
        AgentStepEventType.DEGRADED_MODE_ENTERED: DegradedModeEnteredEvent,
    }

    event_class = event_classes.get(event_type, AgentStepEvent)

    if event_class == AgentStepEvent:
        return AgentStepEvent(type=event_type, step_id=step_id, **kwargs)

    return event_class(type=event_type, step_id=step_id, **kwargs)
