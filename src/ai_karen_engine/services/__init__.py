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
    "transform_web_ui_memory_query",
    "transform_memory_entries_to_web_ui",
    "ensure_js_timestamp",
    "convert_datetime_to_js_timestamp",
    "sanitize_metadata",
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
    # NLP services
    "SpacyService",
    "DistilBertService",
    "NLPServiceManager",
    "NLPHealthMonitor",
    "NLPConfig",
    "SpacyConfig",
    "DistilBertConfig",
    "ParsedMessage",
    "EmbeddingResult",
    "nlp_service_manager",
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
from ai_karen_engine.services.memory_compatibility import (
    transform_web_ui_memory_query,
    transform_memory_entries_to_web_ui,
    ensure_js_timestamp,
    convert_datetime_to_js_timestamp,
    sanitize_metadata,
)

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

# Import NLP services
from ai_karen_engine.services.spacy_service import SpacyService, ParsedMessage
from ai_karen_engine.services.distilbert_service import DistilBertService, EmbeddingResult
from ai_karen_engine.services.nlp_health_monitor import NLPHealthMonitor
from ai_karen_engine.services.nlp_config import NLPConfig, SpacyConfig, DistilBertConfig
from ai_karen_engine.services.nlp_service_manager import NLPServiceManager, nlp_service_manager

# Optional: registry pattern for dynamic dispatch
SERVICES_REGISTRY = {
    "ollama": get_ollama_engine,
    "deepseek": get_deepseek_client,
    "openai": get_openai_service,
    "gemini": get_gemini_service,
}
