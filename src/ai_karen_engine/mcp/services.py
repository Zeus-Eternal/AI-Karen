"""Wrapper services exposing internal tools via MCP."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .registry import ServiceRegistry
from .base import AuthorizationError
from ai_karen_engine.services.knowledge_graph_client import KnowledgeGraphClient
from ai_karen_engine.integrations.llm_utils import LLMUtils


class KnowledgeGraphService:
    """Expose KnowledgeGraphClient methods as MCP service."""

    def __init__(self, kg_client: KnowledgeGraphClient, registry: ServiceRegistry, name: str = "knowledge_graph"):
        self.kg_client = kg_client
        self.registry = registry
        self.registry.register(name, "local", "local", roles=["admin", "user"])
        self.name = name

    def execute_cypher(self, query: str, params: Optional[Dict[str, Any]] = None, rbac_ctx: Optional[Dict[str, Any]] = None) -> Any:
        roles = rbac_ctx.get("roles") if rbac_ctx else []
        if "admin" not in roles and "user" not in roles:
            raise AuthorizationError("RBAC denied")
        return self.kg_client.execute_cypher(query, params)


class LLMService:
    """Expose LLMUtils via MCP."""

    def __init__(self, llm: LLMUtils, registry: ServiceRegistry, name: str = "llm"):
        self.llm = llm
        self.registry = registry
        self.registry.register(name, "local", "local", roles=["admin", "user"])
        self.name = name

    def generate_text(self, prompt: str, provider: Optional[str] = None, rbac_ctx: Optional[Dict[str, Any]] = None) -> str:
        roles = rbac_ctx.get("roles") if rbac_ctx else []
        if "admin" not in roles and "user" not in roles:
            raise AuthorizationError("RBAC denied")
        return self.llm.generate_text(prompt, provider=provider)

