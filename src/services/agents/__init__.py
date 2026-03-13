"""
Agent Architecture System

This package provides a comprehensive agent architecture system with the following components:
- Agent schemas and validation
- Agent metrics and monitoring
- Agent orchestrator for coordination
- Agent memory management
- Agent reasoning capabilities
- Agent tool brokerage
- Agent registry
- Adapters for external frameworks
- Bridges for integration with other systems
"""

# Import Thread Manager components
from .thread_manager_models import (
    ThreadStatus,
    ThreadType,
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
    ThreadManagerError
)

from .thread_manager import (
    ThreadManager
)

# Import key classes and functions from internal modules
from .internal.agent_schemas import (
    AgentStatus,
    TaskStatus,
    MessageStatus,
    PermissionLevel,
    AgentCapability,
    AgentDefinition,
    AgentTask,
    AgentMessage,
    AgentMemory,
    AgentTool,
    AgentResponse,
    AgentSession,
    AgentPermission,
    AgentSchemas
)

# Import Agent UI Service components
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
    AgentUIServiceMetrics
)

from .agent_ui_service import (
    AgentUIServiceInterface,
    AgentUIService
)

from .agent_ui_error_handler import (
    ErrorSeverity,
    ErrorCategory,
    ErrorRecoveryStrategy,
    ErrorContext,
    AgentUIErrorHandler
)

from .internal.agent_validation import (
    AgentValidation
)

from .internal.agent_metrics import (
    AgentMetrics
)

# Import key classes from main agent modules
from .agent_orchestrator import (
    AgentOrchestrator,
    AgentRole,
    AgentPriority
)

from .agent_memory import (
    EnhancedAgentMemory,
    MemoryAccessLevel,
    MemorySharingPolicy,
    MemoryFusionStrategy,
    MemoryOperationType,
    MemorySyncStatus,
    MemoryNamespace,
    MemoryGraphEdge,
    MemorySharingRequest,
    MemoryFusionRequest
)

from .agent_reasoning import (
    AgentReasoning,
    ReasoningType,
    ReasoningStrategy,
    ReasoningConfidence,
    LogicalReasoningEngine,
    CausalReasoningEngine,
    ProbabilisticReasoningEngine,
    StrategicReasoningEngine
)

from .agent_tool_broker import (
    AgentToolBroker,
    ToolStatus,
    AccessDecision,
    SecurityContext
)

# Import communication manager
from .communication import (
    CommunicationManager,
    CommunicationChannelType,
    CommunicationStatus,
    CommunicationError
)

# Import AgentRegistry if available
try:
    from .agent_registry import AgentRegistry
except ImportError:
    AgentRegistry = None

# Import SafetyManager and related enums
try:
    from .safety import (
        SafetyManager,
        SafetyLevel,
        SecurityLevel,
        ThreatType,
        SecurityEvent
    )
except ImportError:
    SafetyManager = None
    SafetyLevel = None
    SecurityLevel = None
    ThreatType = None
    SecurityEvent = None

# Define __all__ to control what gets imported with "from src.services.agents import *"
__all__ = [
    # From thread_manager_models
    "ThreadStatus",
    "ThreadType",
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
    
    # From thread_manager
    "ThreadManager",
    
    # From agent_schemas
    "AgentStatus",
    "TaskStatus",
    "MessageStatus",
    "PermissionLevel",
    "AgentCapability",
    "AgentDefinition",
    "AgentTask",
    "AgentMessage",
    "AgentMemory",
    "AgentTool",
    "AgentResponse",
    "AgentSession",
    "AgentPermission",
    "AgentSchemas",
    
    # From agent_ui_models
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
    
    # From agent_ui_service
    "AgentUIServiceInterface",
    "AgentUIService",
    
    # From agent_ui_error_handler
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorRecoveryStrategy",
    "ErrorContext",
    "AgentUIErrorHandler",
    
    # From agent_validation
    "AgentValidation",
    
    # From agent_metrics
    "AgentMetrics",
    
    # From agent_orchestrator
    "AgentOrchestrator",
    "AgentRole",
    "AgentPriority",
    
    # From agent_memory
    "EnhancedAgentMemory",
    "MemoryAccessLevel",
    "MemorySharingPolicy",
    "MemoryFusionStrategy",
    "MemoryOperationType",
    "MemorySyncStatus",
    "MemoryNamespace",
    "MemoryGraphEdge",
    "MemorySharingRequest",
    "MemoryFusionRequest",
    
    # From agent_reasoning
    "AgentReasoning",
    "ReasoningType",
    "ReasoningStrategy",
    "ReasoningConfidence",
    "LogicalReasoningEngine",
    "CausalReasoningEngine",
    "ProbabilisticReasoningEngine",
    "StrategicReasoningEngine",
    
    # From agent_tool_broker
    "AgentToolBroker",
    "ToolStatus",
    "AccessDecision",
    "SecurityContext",
    
    # From communication
    "CommunicationManager",
    "CommunicationChannelType",
    "CommunicationStatus",
    "CommunicationError",
    
    # From agent_registry
    "AgentRegistry",
    
    # From safety
    "SafetyManager",
    "SafetyLevel",
    "SecurityLevel",
    "ThreatType",
    "SecurityEvent",
]