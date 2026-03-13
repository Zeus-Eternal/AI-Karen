"""
Agent Integration System for AI Karen Engine

This package provides the integration layer between the UI components and the backend
agent orchestration system, supporting multiple execution modes (Native, LangGraph, DeepAgents).
"""

from .integration_service import AgentIntegrationService, get_agent_integration_service
from .models import (
    AgentExecutionMode,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    AgentCapability,
    AgentMetrics,
    AgentConfig,
    StreamChunk,
    AgentError,
    AgentLifecycleEvent
)
from .execution_handlers import (
    NativeExecutionHandler,
    LangGraphExecutionHandler,
    DeepAgentsExecutionHandler,
    get_execution_handler
)
from .lifecycle_manager import AgentLifecycleManager
from .capability_router import AgentCapabilityRouter

__all__ = [
    "AgentIntegrationService",
    "get_agent_integration_service",
    "AgentExecutionMode",
    "AgentRequest",
    "AgentResponse",
    "AgentStatus",
    "AgentCapability",
    "AgentMetrics",
    "AgentConfig",
    "StreamChunk",
    "AgentError",
    "AgentLifecycleEvent",
    "NativeExecutionHandler",
    "LangGraphExecutionHandler",
    "DeepAgentsExecutionHandler",
    "get_execution_handler",
    "AgentLifecycleManager",
    "AgentCapabilityRouter",
]