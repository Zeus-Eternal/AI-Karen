"""MCP module providing gRPC/JSON-RPC clients and service wrappers."""

from .registry import ServiceRegistry
from .base import BaseMCPClient, AuthorizationError
from .grpc_client import GRPCClient
from .json_rpc_client import JSONRPCClient
try:
    from .services import KnowledgeGraphService, LLMService
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
