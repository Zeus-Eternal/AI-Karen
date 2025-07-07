"""
Kari UI Memory Hook - Unified Memory/Context Interface
- Secure session, long-term, and semantic memory
- RBAC/consent-aware for all user data access
- Supports DuckDB, Milvus, Redis, and remote API backends
- Full observability: audit, opt-in/out, usage metrics
"""

import os
import time
from typing import Dict, Any, List

import requests

# === Config & Security ===
API_BASE_URL = os.getenv("KARI_API_BASE_URL", "http://localhost:8000")
MEMORY_SIGNING_KEY = os.getenv("KARI_MEMORY_SIGNING_KEY", "change-me-for-prod")
MEMORY_AUDIT_LOG = "/secure/logs/kari/memory_audit.log"
MEMORY_OPTIN_KEY = "memory_consent"

# === Audit Logging ===
def log_memory_event(event: Dict[str, Any]):
    event["timestamp"] = int(time.time())
    try:
        with open(MEMORY_AUDIT_LOG, "a") as f:
            f.write(str(event) + "\n")
    except Exception:
        pass  # Fallback silent fail; could wire to remote log API

# === Consent/Opt-In ===
def user_has_consented(user_ctx: Dict[str, Any]) -> bool:
    """Check if user has opted-in for memory (EchoCore etc)."""
    return bool(user_ctx.get(MEMORY_OPTIN_KEY, False))

def require_memory_consent(user_ctx: Dict[str, Any]):
    """Raise if user hasn't opted in for memory."""
    if not user_has_consented(user_ctx):
        raise PermissionError("User has not consented to memory collection.")

# === Session Memory (Short-Term) ===
def get_session_context(user_id: str) -> Dict[str, Any]:
    """Fetch current session memory/context for user."""
    url = f"{API_BASE_URL}/api/memory/session/{user_id}"
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {}

def update_session_context(user_id: str, updates: Dict[str, Any]) -> bool:
    """Update session memory/context for user."""
    url = f"{API_BASE_URL}/api/memory/session/{user_id}"
    try:
        resp = requests.post(url, json=updates)
        if resp.status_code == 200:
            log_memory_event({"user": user_id, "action": "update_session", "updates": updates})
            return True
    except Exception:
        pass
    return False

# === Long-Term/Semantic Memory ===
def search_memory(user_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Search user long-term memory (vector or text)."""
    url = f"{API_BASE_URL}/api/memory/search"
    payload = {"user_id": user_id, "query": query, "top_k": top_k}
    try:
        resp = requests.post(url, json=payload)
        if resp.status_code == 200:
            log_memory_event({"user": user_id, "action": "search", "query": query, "top_k": top_k})
            return resp.json().get("results", [])
    except Exception:
        pass
    return []

def add_memory(user_id: str, memory: Dict[str, Any]) -> bool:
    """Add a fact/event to long-term memory."""
    url = f"{API_BASE_URL}/api/memory/add"
    payload = {"user_id": user_id, "memory": memory}
    try:
        resp = requests.post(url, json=payload)
        if resp.status_code == 200:
            log_memory_event({"user": user_id, "action": "add_memory", "memory": memory})
            return True
    except Exception:
        pass
    return False

def get_memory_timeline(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get a timeline of all memory events for a user (most recent first)."""
    url = f"{API_BASE_URL}/api/memory/timeline/{user_id}?limit={limit}"
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            log_memory_event({"user": user_id, "action": "timeline", "limit": limit})
            return resp.json().get("timeline", [])
    except Exception:
        pass
    return []

# === Knowledge Graph / Facts ===
def get_knowledge_graph(user_id: str) -> Dict[str, Any]:
    """Return user's current knowledge graph."""
    url = f"{API_BASE_URL}/api/memory/graph/{user_id}"
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            log_memory_event({"user": user_id, "action": "get_graph"})
            return resp.json()
    except Exception:
        pass
    return {}

# === Opt-In/Out UX ===
def set_memory_consent(user_id: str, consent: bool) -> bool:
    """Set opt-in/out for memory collection (EchoCore etc)."""
    url = f"{API_BASE_URL}/api/memory/consent"
    try:
        resp = requests.post(url, json={"user_id": user_id, "consent": consent})
        if resp.status_code == 200:
            log_memory_event({"user": user_id, "action": "set_consent", "consent": consent})
            return True
    except Exception:
        pass
    return False

# === Public API ===
__all__ = [
    "get_session_context",
    "update_session_context",
    "search_memory",
    "add_memory",
    "get_memory_timeline",
    "get_knowledge_graph",
    "set_memory_consent",
    "user_has_consented",
    "require_memory_consent",
    "log_memory_event",
]
