"""
MCP module providing gRPC/JSON-RPC clients and service wrappers.

Production-ready Model Context Protocol (MCP) implementation with:
- Service registry (Redis-backed with in-memory fallback)
- Multi-protocol clients (gRPC, JSON-RPC)
- Service wrappers (Knowledge Graph, LLM)
- Factory pattern for centralized initialization
- Circuit breakers and retry logic
- Health monitoring and metrics
- FastAPI dependency injection
"""

# Import registry
from ai_karen_engine.mcp.registry import ServiceRegistry, InMemoryServiceRegistry

# Import base classes
from ai_karen_engine.mcp.base import BaseMCPClient, AuthorizationError

# Import clients
from ai_karen_engine.mcp.grpc_client import GRPCClient
from ai_karen_engine.mcp.json_rpc_client import JSONRPCClient

# Import service wrappers (optional dependencies)
try:
    from ai_karen_engine.mcp.services import KnowledgeGraphService, LLMService
except Exception:  # pragma: no cover - optional deps
    KnowledgeGraphService = LLMService = None

# Import factory
from ai_karen_engine.mcp.factory import (
    MCPServiceConfig,
    MCPServiceFactory,
    get_mcp_service_factory,
    get_service_registry,
    get_grpc_client,
    get_json_rpc_client,
    get_knowledge_graph_service,
    get_llm_service,
    initialize_mcp_for_production,
)

# Import dependencies (FastAPI)
from ai_karen_engine.mcp.dependencies import (
    get_service_registry_dependency,
    get_grpc_client_dependency,
    get_json_rpc_client_dependency,
    get_knowledge_graph_service_dependency,
    get_llm_service_dependency,
    get_mcp_factory_dependency,
    get_mcp_health_check,
    get_mcp_metrics,
    get_best_available_client,
    get_rbac_context,
    MCPServiceRegistrar,
    get_mcp_service_registrar,
)

__all__ = [
    # Registry
    "ServiceRegistry",
    "InMemoryServiceRegistry",
    # Base classes
    "BaseMCPClient",
    "AuthorizationError",
    # Clients
    "GRPCClient",
    "JSONRPCClient",
    # Service wrappers
    "KnowledgeGraphService",
    "LLMService",
    # Factory
    "MCPServiceConfig",
    "MCPServiceFactory",
    "get_mcp_service_factory",
    # Factory convenience functions
    "get_service_registry",
    "get_grpc_client",
    "get_json_rpc_client",
    "get_knowledge_graph_service",
    "get_llm_service",
    "initialize_mcp_for_production",
    # Dependencies (FastAPI)
    "get_service_registry_dependency",
    "get_grpc_client_dependency",
    "get_json_rpc_client_dependency",
    "get_knowledge_graph_service_dependency",
    "get_llm_service_dependency",
    "get_mcp_factory_dependency",
    "get_mcp_health_check",
    "get_mcp_metrics",
    "get_best_available_client",
    "get_rbac_context",
    "MCPServiceRegistrar",
    "get_mcp_service_registrar",
]
