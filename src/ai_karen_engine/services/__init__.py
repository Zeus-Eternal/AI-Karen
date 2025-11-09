"""
Service utilities for Kari AI

Production-ready service layer with:
- Comprehensive factory pattern for all services
- FastAPI dependency injection
- Intelligent service orchestration
- Health monitoring and metrics
- Graceful degradation
"""

# Import factory and dependencies first
from ai_karen_engine.services.factory import (
    ServicesConfig,
    ServicesFactory,
    get_services_factory,
    initialize_services_for_production,
)

from ai_karen_engine.services.dependencies import (
    # Factory
    get_services_factory_dependency,
    # AI Services
    get_ai_orchestrator_dependency,
    get_model_library_dependency,
    get_model_orchestrator_dependency,
    get_intelligent_router_dependency,
    # Memory Services
    get_memory_service_dependency,
    get_enhanced_memory_dependency,
    get_integrated_memory_dependency,
    # NLP Services
    get_nlp_manager_dependency,
    # Knowledge Services
    get_knowledge_graph_dependency,
    # Analytics Services
    get_analytics_service_dependency,
    get_analytics_dashboard_dependency,
    get_metrics_service_dependency,
    # Plugin & Tool Services
    get_plugin_service_dependency,
    get_tool_service_dependency,
    # Database Services
    get_database_health_dependency,
    get_database_optimization_dependency,
    get_database_query_cache_dependency,
    # Auth & Security Services
    get_auth_service_dependency,
    # Cache Services
    get_production_cache_dependency,
    get_smart_cache_dependency,
    get_integrated_cache_dependency,
    # Monitoring Services
    get_production_monitoring_dependency,
    get_performance_monitor_dependency,
    get_health_checker_dependency,
    # Error & Recovery Services
    get_error_recovery_dependency,
    get_graceful_degradation_dependency,
    get_fallback_provider_dependency,
    # Provider Services
    get_provider_registry_dependency,
    get_provider_health_monitor_dependency,
    # Conversation Services
    get_conversation_service_dependency,
    get_context_processor_dependency,
    # User Services
    get_user_service_dependency,
    get_persona_service_dependency,
    # System Services
    get_settings_manager_dependency,
    get_secret_manager_dependency,
    # Health & Metrics
    get_services_health_check,
    get_services_metrics,
    # Composite
    get_core_services,
)

__all__ = [
    # Factory & Dependencies
    "ServicesConfig",
    "ServicesFactory",
    "get_services_factory",
    "initialize_services_for_production",
    # FastAPI Dependencies - Factory
    "get_services_factory_dependency",
    # FastAPI Dependencies - AI Services
    "get_ai_orchestrator_dependency",
    "get_model_library_dependency",
    "get_model_orchestrator_dependency",
    "get_intelligent_router_dependency",
    # FastAPI Dependencies - Memory Services
    "get_memory_service_dependency",
    "get_enhanced_memory_dependency",
    "get_integrated_memory_dependency",
    # FastAPI Dependencies - NLP Services
    "get_nlp_manager_dependency",
    # FastAPI Dependencies - Knowledge Services
    "get_knowledge_graph_dependency",
    # FastAPI Dependencies - Analytics Services
    "get_analytics_service_dependency",
    "get_analytics_dashboard_dependency",
    "get_metrics_service_dependency",
    # FastAPI Dependencies - Plugin & Tool Services
    "get_plugin_service_dependency",
    "get_tool_service_dependency",
    # FastAPI Dependencies - Database Services
    "get_database_health_dependency",
    "get_database_optimization_dependency",
    "get_database_query_cache_dependency",
    # FastAPI Dependencies - Auth & Security Services
    "get_auth_service_dependency",
    # FastAPI Dependencies - Cache Services
    "get_production_cache_dependency",
    "get_smart_cache_dependency",
    "get_integrated_cache_dependency",
    # FastAPI Dependencies - Monitoring Services
    "get_production_monitoring_dependency",
    "get_performance_monitor_dependency",
    "get_health_checker_dependency",
    # FastAPI Dependencies - Error & Recovery Services
    "get_error_recovery_dependency",
    "get_graceful_degradation_dependency",
    "get_fallback_provider_dependency",
    # FastAPI Dependencies - Provider Services
    "get_provider_registry_dependency",
    "get_provider_health_monitor_dependency",
    # FastAPI Dependencies - Conversation Services
    "get_conversation_service_dependency",
    "get_context_processor_dependency",
    # FastAPI Dependencies - User Services
    "get_user_service_dependency",
    "get_persona_service_dependency",
    # FastAPI Dependencies - System Services
    "get_settings_manager_dependency",
    "get_secret_manager_dependency",
    # FastAPI Dependencies - Health & Metrics
    "get_services_health_check",
    "get_services_metrics",
    # FastAPI Dependencies - Composite
    "get_core_services",
    # Legacy exports for backward compatibility
    "get_llamacpp_engine",
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
    "get_nlp_service_manager",
    "reset_nlp_service_manager",
    "NLPHealthMonitor",
    "NLPConfig",
    "SpacyConfig",
    "DistilBertConfig",
    "ParsedMessage",
    "EmbeddingResult",
    "nlp_service_manager",
    # Model Library service
    "ModelLibraryService",
    "ModelInfo",
    "DownloadTask",
    "ModelMetadata",
    "ModelDownloadManager",
    "ModelMetadataService",
]

# Legacy compatibility functions

def get_llamacpp_engine():
    from ai_karen_engine.inference.llamacpp_runtime import LlamaCppRuntime
    return LlamaCppRuntime

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
from ai_karen_engine.services.ai_orchestrator.ai_orchestrator import (
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
from ai_karen_engine.services.nlp_service_manager import (
    NLPServiceManager,
    get_nlp_service_manager,
    reset_nlp_service_manager,
    nlp_service_manager,
)

# Model Library service
from ai_karen_engine.services.model_library_service import (
    ModelLibraryService,
    ModelInfo,
    DownloadTask,
    ModelMetadata,
    ModelDownloadManager,
    ModelMetadataService,
)

# Optional: registry pattern for dynamic dispatch
SERVICES_REGISTRY = {
    "llama-cpp": get_llamacpp_engine,
    "deepseek": get_deepseek_client,
    "openai": get_openai_service,
    "gemini": get_gemini_service,
}
