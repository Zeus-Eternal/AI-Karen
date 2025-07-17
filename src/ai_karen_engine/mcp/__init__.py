"""MCP module providing gRPC/JSON-RPC clients and service wrappers."""

from ai_karen_engine.mcp.registry import ServiceRegistry
from ai_karen_engine.mcp.base import BaseMCPClient, AuthorizationError
from ai_karen_engine.mcp.grpc_client import GRPCClient
from ai_karen_engine.mcp.json_rpc_client import JSONRPCClient
try:
    from ai_karen_engine.mcp.services import KnowledgeGraphService, LLMService
except Exception:  # pragma: no cover - optional deps
    KnowledgeGraphService = LLMService = None

__all__ = [
    "ServiceRegistry",
    "BaseMCPClient",
    "AuthorizationError",
    "GRPCClient",
    "JSONRPCClient",
    "KnowledgeGraphService",
    "LLMService",
]
