"""
FastAPI dependency providers for MCP services.

Provides singleton instances of all MCP services for dependency injection.
"""

from functools import lru_cache
from typing import Optional, Dict, Any

from ai_karen_engine.mcp.factory import (
    get_service_registry as _get_service_registry,
    get_grpc_client as _get_grpc_client,
    get_json_rpc_client as _get_json_rpc_client,
    get_knowledge_graph_service as _get_knowledge_graph_service,
    get_llm_service as _get_llm_service,
    get_mcp_service_factory,
)


# Service registry dependency
@lru_cache()
def get_service_registry_dependency():
    """
    FastAPI dependency for service registry.

    Returns:
        ServiceRegistry or InMemoryServiceRegistry instance

    Usage:
        @app.get("/mcp/services")
        def list_services(
            registry = Depends(get_service_registry_dependency)
        ):
            return registry.list()
    """
    return _get_service_registry()


# Client dependencies
@lru_cache()
def get_grpc_client_dependency():
    """
    FastAPI dependency for gRPC client.

    Returns:
        GRPCClient instance or None if unavailable

    Usage:
        @app.post("/mcp/grpc/call")
        def call_grpc_service(
            service: str,
            method: str,
            payload: bytes,
            client = Depends(get_grpc_client_dependency)
        ):
            if not client:
                raise HTTPException(status_code=503, detail="gRPC client unavailable")
            return client.call(service, method, payload, token="...")
    """
    return _get_grpc_client()


@lru_cache()
def get_json_rpc_client_dependency():
    """
    FastAPI dependency for JSON-RPC client.

    Returns:
        JSONRPCClient instance or None if unavailable

    Usage:
        @app.post("/mcp/jsonrpc/call")
        def call_jsonrpc_service(
            service: str,
            method: str,
            params: dict,
            client = Depends(get_json_rpc_client_dependency)
        ):
            if not client:
                raise HTTPException(status_code=503, detail="JSON-RPC client unavailable")
            return client.call(service, method, params, token="...")
    """
    return _get_json_rpc_client()


# Service wrapper dependencies
@lru_cache()
def get_knowledge_graph_service_dependency():
    """
    FastAPI dependency for knowledge graph service.

    Returns:
        KnowledgeGraphService instance or None if unavailable

    Usage:
        @app.post("/mcp/kg/query")
        def execute_cypher_query(
            query: str,
            params: Optional[dict] = None,
            service = Depends(get_knowledge_graph_service_dependency)
        ):
            if not service:
                raise HTTPException(status_code=503, detail="Knowledge graph service unavailable")
            return service.execute_cypher(query, params, rbac_ctx={"roles": ["user"]})
    """
    return _get_knowledge_graph_service()


@lru_cache()
def get_llm_service_dependency():
    """
    FastAPI dependency for LLM service.

    Returns:
        LLMService instance or None if unavailable

    Usage:
        @app.post("/mcp/llm/generate")
        def generate_text(
            prompt: str,
            provider: Optional[str] = None,
            service = Depends(get_llm_service_dependency)
        ):
            if not service:
                raise HTTPException(status_code=503, detail="LLM service unavailable")
            return service.generate_text(prompt, provider, rbac_ctx={"roles": ["user"]})
    """
    return _get_llm_service()


# Factory dependency
@lru_cache()
def get_mcp_factory_dependency():
    """
    FastAPI dependency for MCP service factory.

    Returns:
        MCPServiceFactory instance

    Usage:
        @app.get("/mcp/status")
        def get_mcp_status(
            factory = Depends(get_mcp_factory_dependency)
        ):
            return factory.health_check()
    """
    return get_mcp_service_factory()


# Health check dependency
def get_mcp_health_check():
    """
    FastAPI dependency for MCP service health check.

    Returns:
        Dictionary of MCP service health statuses

    Usage:
        @app.get("/health/mcp")
        def mcp_health(health: dict = Depends(get_mcp_health_check)):
            return health
    """
    factory = get_mcp_service_factory()
    return factory.health_check()


# Metrics dependency
def get_mcp_metrics():
    """
    FastAPI dependency for MCP service metrics.

    Returns:
        Dictionary of MCP service metrics

    Usage:
        @app.get("/metrics/mcp")
        def mcp_metrics(metrics: dict = Depends(get_mcp_metrics)):
            return metrics
    """
    factory = get_mcp_service_factory()
    return factory.get_metrics()


# Combined client dependency (returns best available client)
def get_best_available_client(prefer_grpc: bool = True):
    """
    FastAPI dependency that returns the best available client.

    Preference order (configurable):
    - prefer_grpc=True: gRPC client first, JSON-RPC as fallback
    - prefer_grpc=False: JSON-RPC client first, gRPC as fallback

    Args:
        prefer_grpc: Whether to prefer gRPC over JSON-RPC

    Returns:
        Best available client instance or None

    Usage:
        @app.post("/mcp/call")
        def call_service(
            service: str,
            method: str,
            data: dict,
            client = Depends(get_best_available_client)
        ):
            if not client:
                raise HTTPException(status_code=503, detail="No MCP client available")
            # Use client based on its type
            if isinstance(client, GRPCClient):
                return client.call(service, method, json.dumps(data).encode(), token="...")
            else:
                return client.call(service, method, data, token="...")
    """
    factory = get_mcp_service_factory()

    clients_to_try = (
        ["grpc_client", "json_rpc_client"]
        if prefer_grpc
        else ["json_rpc_client", "grpc_client"]
    )

    for client_name in clients_to_try:
        client = factory.get_client(client_name)
        if client:
            return client

        # Try to create if not exists
        try:
            if client_name == "grpc_client":
                client = factory.create_grpc_client()
            elif client_name == "json_rpc_client":
                client = factory.create_json_rpc_client()

            if client:
                return client
        except Exception:
            continue

    return None


# RBAC context dependency
def get_rbac_context(
    token: Optional[str] = None, role: Optional[str] = None
) -> Dict[str, Any]:
    """
    FastAPI dependency for extracting RBAC context from request.

    Args:
        token: Optional authentication token from request
        role: Optional role from request (header, query, etc.)

    Returns:
        RBAC context dictionary

    Usage:
        @app.post("/mcp/service/call")
        def call_service(
            service_name: str,
            rbac_ctx: dict = Depends(get_rbac_context),
            service = Depends(get_knowledge_graph_service_dependency)
        ):
            return service.execute_cypher("MATCH (n) RETURN n", rbac_ctx=rbac_ctx)
    """
    return {"token": token or "default-token", "roles": [role or "user"]}


# Service registration helper
class MCPServiceRegistrar:
    """
    Helper for registering MCP services in FastAPI routes.

    Usage:
        @app.on_event("startup")
        def register_services():
            registrar = MCPServiceRegistrar()
            registrar.register_http_service(
                name="my_service",
                endpoint="http://localhost:8080/rpc",
                kind="jsonrpc",
                roles=["admin", "user"]
            )
    """

    def __init__(self):
        self.factory = get_mcp_service_factory()
        self.registry = self.factory.get_service("service_registry")
        if not self.registry:
            self.registry = self.factory.create_service_registry()

    def register_http_service(
        self,
        name: str,
        endpoint: str,
        kind: str = "jsonrpc",
        roles: Optional[list] = None,
    ) -> None:
        """Register an HTTP-based service (JSON-RPC)."""
        if not self.registry:
            raise RuntimeError("Service registry not available")
        self.registry.register(name, endpoint, kind, roles or ["user"])

    def register_grpc_service(
        self, name: str, endpoint: str, roles: Optional[list] = None
    ) -> None:
        """Register a gRPC-based service."""
        if not self.registry:
            raise RuntimeError("Service registry not available")
        self.registry.register(name, endpoint, "grpc", roles or ["user"])

    def deregister_service(self, name: str) -> None:
        """Deregister a service."""
        if not self.registry:
            raise RuntimeError("Service registry not available")
        self.registry.deregister(name)

    def list_services(self) -> dict:
        """List all registered services."""
        if not self.registry:
            raise RuntimeError("Service registry not available")
        return self.registry.list()


def get_mcp_service_registrar() -> MCPServiceRegistrar:
    """
    FastAPI dependency for MCP service registrar.

    Returns:
        MCPServiceRegistrar instance

    Usage:
        @app.post("/mcp/services/register")
        def register_service(
            name: str,
            endpoint: str,
            kind: str,
            registrar: MCPServiceRegistrar = Depends(get_mcp_service_registrar)
        ):
            registrar.register_http_service(name, endpoint, kind)
            return {"status": "registered"}
    """
    return MCPServiceRegistrar()


__all__ = [
    # Registry dependencies
    "get_service_registry_dependency",
    # Client dependencies
    "get_grpc_client_dependency",
    "get_json_rpc_client_dependency",
    # Service wrapper dependencies
    "get_knowledge_graph_service_dependency",
    "get_llm_service_dependency",
    # Factory dependencies
    "get_mcp_factory_dependency",
    "get_mcp_health_check",
    "get_mcp_metrics",
    # Utilities
    "get_best_available_client",
    "get_rbac_context",
    "MCPServiceRegistrar",
    "get_mcp_service_registrar",
]
