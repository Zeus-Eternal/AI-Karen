"""
Kari Knowledge Graph Panel Logic
- Visualizes relationships, facts, and concepts (Neo4j/Milvus)
- RBAC: user, admin, analyst
- Auditable and query-driven
"""

from typing import Dict, Any, List
from ui.hooks.rbac import require_roles
from ui.utils.api import fetch_knowledge_graph, fetch_audit_logs

def get_knowledge_graph(user_ctx: Dict, query: str = "") -> Dict[str, Any]:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin", "analyst"]):
        raise PermissionError("Insufficient privileges for knowledge graph access.")
    return fetch_knowledge_graph(user_ctx.get("user_id"), query=query)

def get_kg_audit_trail(user_ctx: Dict, limit: int = 25) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["admin", "analyst"]):
        raise PermissionError("Insufficient privileges for KG audit.")
    return fetch_audit_logs(category="knowledge_graph", user_id=user_ctx["user_id"])[-limit:][::-1]
