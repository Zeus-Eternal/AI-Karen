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
from .agent_ui_models import (
    ExecutionMode,
    UIComponentType,
    ContentType,
    LayoutType,
    OutputProfile,
    SendMessageRequest,
    SendMessageResponse,
    CreateDeepTaskRequest,
    CreateDeepTaskResponse,
    GetTaskProgressRequest,
    GetTaskProgressResponse,
    CancelTaskRequest,
    CancelTaskResponse,
    AgentUIRequest,
    AgentUIResponse,
    InteractiveElement,
    ResponseMetadata,
    TaskProgress,
    AgentUIError,
    AgentUIServiceConfig,
    AgentUIServiceStatus,
    AgentUIServiceMetrics,
)
from .agent_ui_service import AgentUIServiceInterface, AgentUIService
from .agent_ui_integration import AgentUIIntegration
from .agent_ui_error_handler import (
    ErrorSeverity,
    ErrorCategory,
    ErrorRecoveryStrategy,
    ErrorContext,
    AgentUIErrorHandler,
)
from .agent_task_router import AgentTaskRouter
from .agent_memory_fusion import AgentMemoryFusion
from .agent_monitor import AgentMonitor
from .agent_echo_core import AgentEchoCore
from .communication import (
    CommunicationManager,
    CommunicationChannelType,
    CommunicationStatus,
    CommunicationError,
)
from .safety import (
    SafetyManager,
    SafetyLevel as CoreSafetyLevel,
    SecurityLevel,
    ThreatType,
    SecurityEvent,
)

try:
    from .agent_tool_broker import AgentToolBroker, ToolStatus, AccessDecision, SecurityContext
except Exception:  # Optional dependency chain
    AgentToolBroker = None
    ToolStatus = None
    AccessDecision = None
    SecurityContext = None

try:
    from .agent_registry import (
        AgentRegistry,
        AgentHealthStatus,
        AgentLifecycleEvent as AgentRegistryLifecycleEvent,
    )
except Exception:  # Optional dependency chain
    AgentRegistry = None
    AgentHealthStatus = None
    AgentRegistryLifecycleEvent = None
from .thread_manager import ThreadManager
from .thread_manager_models import (
    ThreadStatus,
    ThreadType,
    ThreadMetadata,
    Thread,
    SessionThreadMapping,
    CreateThreadRequest,
    CreateThreadResponse,
    GetThreadRequest,
    GetThreadResponse,
    UpdateThreadRequest,
    UpdateThreadResponse,
    DeleteThreadRequest,
    DeleteThreadResponse,
    ListThreadsRequest,
    ListThreadsResponse,
    GetSessionThreadsRequest,
    GetSessionThreadsResponse,
    SetPrimaryThreadRequest,
    SetPrimaryThreadResponse,
    ThreadManagerConfig,
    ThreadManagerStatus,
    ThreadManagerMetrics,
    ThreadManagerError,
)

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
    "ThreadManager",
    "ExecutionMode",
    "UIComponentType",
    "ContentType",
    "LayoutType",
    "OutputProfile",
    "SendMessageRequest",
    "SendMessageResponse",
    "CreateDeepTaskRequest",
    "CreateDeepTaskResponse",
    "GetTaskProgressRequest",
    "GetTaskProgressResponse",
    "CancelTaskRequest",
    "CancelTaskResponse",
    "AgentUIRequest",
    "AgentUIResponse",
    "InteractiveElement",
    "ResponseMetadata",
    "TaskProgress",
    "AgentUIError",
    "AgentUIServiceConfig",
    "AgentUIServiceStatus",
    "AgentUIServiceMetrics",
    "AgentUIServiceInterface",
    "AgentUIService",
    "AgentUIIntegration",
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorRecoveryStrategy",
    "ErrorContext",
    "AgentUIErrorHandler",
    "AgentTaskRouter",
    "AgentMemoryFusion",
    "AgentMonitor",
    "AgentEchoCore",
    "CommunicationManager",
    "CommunicationChannelType",
    "CommunicationStatus",
    "CommunicationError",
    "SafetyManager",
    "CoreSafetyLevel",
    "SecurityLevel",
    "ThreatType",
    "SecurityEvent",
    "ThreadStatus",
    "ThreadType",
    "ThreadMetadata",
    "Thread",
    "SessionThreadMapping",
    "CreateThreadRequest",
    "CreateThreadResponse",
    "GetThreadRequest",
    "GetThreadResponse",
    "UpdateThreadRequest",
    "UpdateThreadResponse",
    "DeleteThreadRequest",
    "DeleteThreadResponse",
    "ListThreadsRequest",
    "ListThreadsResponse",
    "GetSessionThreadsRequest",
    "GetSessionThreadsResponse",
    "SetPrimaryThreadRequest",
    "SetPrimaryThreadResponse",
    "ThreadManagerConfig",
    "ThreadManagerStatus",
    "ThreadManagerMetrics",
    "ThreadManagerError",
]

if AgentToolBroker is not None:
    __all__.extend([
        "AgentToolBroker",
        "ToolStatus",
        "AccessDecision",
        "SecurityContext",
    ])

if AgentRegistry is not None:
    __all__.extend([
        "AgentRegistry",
        "AgentHealthStatus",
        "AgentRegistryLifecycleEvent",
    ])
