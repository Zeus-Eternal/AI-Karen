"""Service utilities for Kari AI (compatibility wrappers, lazy-load, zero circular imports)."""

__all__ = [
    "get_ollama_engine",
    "get_deepseek_client",
    "get_openai_service",
    "get_gemini_service",
    "AIOrchestrator",
    "FlowManager",
    "DecisionEngine",
    "ContextManager",
    "PromptManager",
    # Plugin services
    "PluginService",
    "PluginRegistry",
    "PluginExecutionEngine",
    "get_plugin_service",
    "initialize_plugin_service",
    "discover_and_register_all_plugins",
    "execute_plugin_simple",
    "get_plugin_marketplace_info",
    # Memory service
    "WebUIMemoryService",
    # Tool services
    "ToolService",
    "ToolRegistry",
    "BaseTool",
    "ToolMetadata",
    "ToolInput",
    "ToolOutput",
    "ToolCategory",
    "ToolStatus",
    "get_tool_service",
    "initialize_tool_service",
    # Tool registry functions
    "register_core_tools",
    "unregister_core_tools",
    "get_core_tool_names",
    "initialize_core_tools",
    # Analytics service
    "AnalyticsService",
    "get_analytics_service",
    "initialize_analytics_service",
    "PerformanceTimer",
    "track_performance",
    # Analytics dashboard
    "AnalyticsDashboard",
    "get_analytics_dashboard",
    "initialize_analytics_dashboard",
]

def get_ollama_engine():
    from ai_karen_engine.services import ollama_engine
    return ollama_engine

def get_deepseek_client():
    from ai_karen_engine.services import deepseek_client
    return deepseek_client

def get_openai_service():
    from ai_karen_engine.services import openai
    return openai

def get_gemini_service():
    from ai_karen_engine.services import gemini
    return gemini

# Import AI Orchestrator components
from ai_karen_engine.services.ai_orchestrator import (
    AIOrchestrator,
    FlowManager,
    DecisionEngine,
    ContextManager,
    PromptManager
)

# Import Plugin services
from ai_karen_engine.services.plugin_service import (
    PluginService,
    get_plugin_service,
    initialize_plugin_service,
    discover_and_register_all_plugins,
    execute_plugin_simple,
    get_plugin_marketplace_info
)
from ai_karen_engine.services.plugin_registry import PluginRegistry
from ai_karen_engine.services.plugin_execution import PluginExecutionEngine

# Import Memory service
from ai_karen_engine.services.memory_service import WebUIMemoryService

# Import Tool services
from ai_karen_engine.services.tool_service import (
    ToolService,
    ToolRegistry,
    BaseTool,
    ToolMetadata,
    ToolInput,
    ToolOutput,
    ToolCategory,
    ToolStatus,
    get_tool_service,
    initialize_tool_service
)

# Import Tool registry functions
from ai_karen_engine.services.tools import (
    register_core_tools,
    unregister_core_tools,
    get_core_tool_names,
    initialize_core_tools
)

# Import Analytics service
from ai_karen_engine.services.analytics_service import (
    AnalyticsService,
    get_analytics_service,
    initialize_analytics_service,
    PerformanceTimer,
    track_performance
)

# Import Analytics dashboard
from ai_karen_engine.services.analytics_dashboard import (
    AnalyticsDashboard,
    get_analytics_dashboard,
    initialize_analytics_dashboard
)

# Optional: registry pattern for dynamic dispatch
SERVICES_REGISTRY = {
    "ollama": get_ollama_engine,
    "deepseek": get_deepseek_client,
    "openai": get_openai_service,
    "gemini": get_gemini_service,
}
