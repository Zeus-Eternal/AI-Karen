"""
Kari UI Universal API Utility
- Centralized fetcher for all UI layers (mobile, desktop, admin)
- Handles RBAC tokens, error translation, observability, and service pings
- Enterprise-grade: supports multi-tenant, plugin, and fallback local APIs
"""

import datetime
import os
import threading
import time
import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from typing import Any, Dict, List, Optional, Set, Union


from cachetools import TTLCache, cached

from ui_logic.models.announcement import Announcement

# ======= UI/API CONFIG =======
API_BASE = os.getenv("KARI_API_BASE", "http://localhost:8000/api")
TIMEOUT = float(os.getenv("KARI_API_TIMEOUT", "30"))

# ======= Announcement Cache =======
_ann_cache = TTLCache(maxsize=100, ttl=60)

# ======= In-Memory RBAC for Admin Panel (thread-safe, hot-swap DB later) =======
_USERS_ROLES: Dict[str, Set[str]] = {}
_ROLE_POLICIES: Dict[str, Set[str]] = {}
_LOCK = threading.RLock()


def fetch_user_roles(user_id: Optional[str] = None) -> Dict[str, List[str]]:
    with _LOCK:
        if user_id:
            return {user_id: list(_USERS_ROLES.get(user_id, set()))}
        return {uid: list(roles) for uid, roles in _USERS_ROLES.items()}


def update_user_roles(user_id: str, roles: List[str]) -> bool:
    if not user_id or not isinstance(roles, list):
        raise ValueError("user_id and roles are required")
    with _LOCK:
        _USERS_ROLES[user_id] = set(roles)
    return True


def fetch_role_policies(role: Optional[str] = None) -> Dict[str, List[str]]:
    with _LOCK:
        if role:
            return {role: list(_ROLE_POLICIES.get(role, set()))}
        return {r: list(policies) for r, policies in _ROLE_POLICIES.items()}


def update_role_policies(role: str, policies: List[str]) -> bool:
    if not role or not isinstance(policies, list):
        raise ValueError("role and policies are required")
    with _LOCK:
        _ROLE_POLICIES[role] = set(policies)
    return True


def add_role_to_user(user_id: str, role: str) -> bool:
    if not user_id or not role:
        raise ValueError("user_id and role are required")
    with _LOCK:
        _USERS_ROLES.setdefault(user_id, set()).add(role)
    return True


def remove_role_from_user(user_id: str, role: str) -> bool:
    with _LOCK:
        roles = _USERS_ROLES.get(user_id)
        if roles and role in roles:
            roles.remove(role)
            if not roles:
                del _USERS_ROLES[user_id]
    return True


def add_policy_to_role(role: str, policy: str) -> bool:
    if not role or not policy:
        raise ValueError("role and policy are required")
    with _LOCK:
        _ROLE_POLICIES.setdefault(role, set()).add(policy)
    return True


def remove_policy_from_role(role: str, policy: str) -> bool:
    with _LOCK:
        policies = _ROLE_POLICIES.get(role)
        if policies and policy in policies:
            policies.remove(policy)
            if not policies:
                del _ROLE_POLICIES[role]
    return True


def list_all_roles() -> List[str]:
    with _LOCK:
        return list(_ROLE_POLICIES.keys())


def list_all_users() -> List[str]:
    with _LOCK:
        return list(_USERS_ROLES.keys())


# ======= HTTP API UNIVERSAL UTILS =======
def get_auth_headers(
    token: Optional[str] = None, org: Optional[str] = None
) -> Dict[str, str]:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if org:
        headers["X-Org-ID"] = org
    return headers


def handle_response(resp: requests.Response) -> Any:
    try:
        resp.raise_for_status()
        if "application/json" in resp.headers.get("Content-Type", ""):
            return resp.json()
        return resp.text
    except requests.HTTPError as e:
        raise RuntimeError(f"API error: {e.response.status_code} {e.response.text}")

        
def _safe_request(method: str, url: str, **kwargs) -> requests.Response:
    """Wrapper around ``requests`` with simple retry semantics."""
    attempts = 0
    while True:
        try:
            return requests.request(method, url, **kwargs)
        except requests.RequestException:
            attempts += 1
            if attempts >= 3:
                raise
            time.sleep(0.5 * attempts)
def api_get(
    path: str,
    params: Optional[Dict[str, Any]] = None,
    token: Optional[str] = None,
    org: Optional[str] = None,
    timeout: Optional[float] = None,
) -> Any:
    url = f"{API_BASE.rstrip('/')}/{path.lstrip('/')}"
    headers = get_auth_headers(token, org)
    resp = _safe_request(
        "get",
        url,
        headers=headers,
        params=params,
        timeout=timeout or TIMEOUT,
    )
    return handle_response(resp)


def api_post(
    path: str,
    data: Optional[Union[Dict, str]] = None,
    token: Optional[str] = None,
    org: Optional[str] = None,
    timeout: Optional[float] = None,
    json: bool = True,
    files: Optional[Dict] = None,
) -> Any:
    url = f"{API_BASE.rstrip('/')}/{path.lstrip('/')}"
    headers = get_auth_headers(token, org)
    if files:
      
        resp = _safe_request(
            "post",
            url,
            headers=headers,
            files=files,
            data=data,
            timeout=timeout or TIMEOUT,
        )
    else:
        if json:
            resp = _safe_request(
                "post",
                url,
                headers=headers,
                json=data,
                timeout=timeout or TIMEOUT,
            )
        else:
            resp = _safe_request(
                "post",
                url,
                headers=headers,
                data=data,
                timeout=timeout or TIMEOUT,
            )
    return handle_response(resp)


def api_put(
    path: str,
    data: Optional[Union[Dict, str]] = None,
    token: Optional[str] = None,
    org: Optional[str] = None,
    timeout: Optional[float] = None,
    json: bool = True,
) -> Any:
    url = f"{API_BASE.rstrip('/')}/{path.lstrip('/')}"
    headers = get_auth_headers(token, org)
    if json:
        resp = _safe_request(
            "put",
            url,
            headers=headers,
            json=data,
            timeout=timeout or TIMEOUT,
        )
    else:
        resp = _safe_request(
            "put",
            url,
            headers=headers,
            data=data,
            timeout=timeout or TIMEOUT,
        )
    return handle_response(resp)


def api_delete(
    path: str,
    token: Optional[str] = None,
    org: Optional[str] = None,
    timeout: Optional[float] = None,
) -> Any:
    url = f"{API_BASE.rstrip('/')}/{path.lstrip('/')}"
    headers = get_auth_headers(token, org)
    resp = _safe_request(
        "delete",
        url,
        headers=headers,
        timeout=timeout or TIMEOUT,
    )
    return handle_response(resp)


# ======= HIGH-LEVEL UI LOGIC (AUDIT, PLUGIN, HEALTH, PING, ANNOUNCEMENTS) =======
def fetch_audit_logs(
    category: Optional[str] = None,
    user_id: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    token: Optional[str] = None,
    org: Optional[str] = None,
) -> Any:
    params = {"limit": limit}
    if category:
        params["category"] = category
    if user_id:
        params["user_id"] = user_id
    if search:
        params["search"] = search
    return api_get("audit/logs", params=params, token=token, org=org)


@cached(_ann_cache)
def fetch_announcements(
    limit: int = 10, token: Optional[str] = None, org: Optional[str] = None
) -> List[Announcement]:
    """Return a list of ``Announcement`` objects or an empty list if the endpoint is missing."""
    try:
        data = api_get("announcements", params={"limit": limit}, token=token, org=org)
        if not isinstance(data, list):
            return []
        return [Announcement.from_api(a) for a in data]
    except RuntimeError as e:  # 404 when endpoint isn't implemented
        if "404" in str(e):
            return []
        raise


def api_plugin_action(
    plugin: str,
    action: str,
    payload: Optional[dict] = None,
    token: Optional[str] = None,
    org: Optional[str] = None,
) -> Any:
    return api_post(f"plugins/{plugin}/{action}", data=payload, token=token, org=org)


def api_health(token: Optional[str] = None) -> Any:
    return api_get("health", token=token)


def api_list_plugins(token: Optional[str] = None, org: Optional[str] = None) -> Any:
    return api_get("plugins", token=token, org=org)


def api_upload_file(
    path: str, file_path: str, token: Optional[str] = None, org: Optional[str] = None
) -> Any:
    with open(file_path, "rb") as f:
        files = {"file": f}
        return api_post(path, files=files, token=token, org=org, json=False)


def ping_services(timeout: float = 2.0) -> dict:
    status = {}
    try:
        health = api_health()
        status["api"] = "ok" if health else "down"
    except Exception as ex:
        status["api"] = f"error: {ex}"
    try:
        from pymilvus import connections

        t0 = time.time()
        connections.connect(alias="default")
        s = connections.has_connection("default")
        status["milvus"] = "ok" if s else "down"
        status["milvus_latency_ms"] = int((time.time() - t0) * 1000)
    except Exception as ex:
        status["milvus"] = f"error: {ex}"
    try:
        import redis

        redis_url = os.getenv("REDIS_URL")
        client = redis.Redis.from_url(redis_url) if redis_url else redis.Redis()
        pong = client.ping()
        status["redis"] = "ok" if pong else "down"
    except Exception as ex:
        status["redis"] = f"error: {ex}"
    try:
        import duckdb

        db = duckdb.connect(database=":memory:", read_only=False)
        db.execute("SELECT 1;")
        status["duckdb"] = "ok"
    except Exception as ex:
        status["duckdb"] = f"error: {ex}"
    try:
        import psycopg

        with psycopg.connect(
            dbname=os.getenv("POSTGRES_DB", "postgres"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            connect_timeout=timeout,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
        status["postgres"] = "ok"
    except Exception as ex:
        status["postgres"] = f"error: {ex}"
    llm_url = os.getenv("KARI_LLM_URL")
    if llm_url:
        try:
          
            resp = _safe_request(
                "get",
                f"{llm_url.rstrip('/')}/health",
                timeout=timeout,
            )
            status["llm"] = "ok" if resp.status_code == 200 else f"error: {resp.status_code}"
        except Exception as ex:
            status["llm"] = f"error: {ex}"
    return status


# ========================= ORG ADMIN (Multi-Org, Multi-Tenant) =========================

_ORG_USERS: Dict[str, Set[str]] = {}
_ORG_SETTINGS: Dict[str, Dict[str, Any]] = {}


def fetch_org_users(org_id: str) -> List[str]:
    if not org_id:
        raise ValueError("org_id required")
    with _LOCK:
        return list(_ORG_USERS.get(org_id, set()))


def add_org_user(org_id: str, user_id: str) -> bool:
    if not org_id or not user_id:
        raise ValueError("org_id and user_id required")
    with _LOCK:
        _ORG_USERS.setdefault(org_id, set()).add(user_id)
    return True


def update_org_user(
    org_id: str, user_id: str, roles: Optional[List[str]] = None
) -> bool:
    if not org_id or not user_id:
        raise ValueError("org_id and user_id required")
    with _LOCK:
        _ORG_USERS.setdefault(org_id, set()).add(user_id)
        if roles is not None:
            _USERS_ROLES[user_id] = set(roles)
    return True


def remove_org_user(org_id: str, user_id: str) -> bool:
    if not org_id or not user_id:
        raise ValueError("org_id and user_id required")
    with _LOCK:
        users = _ORG_USERS.get(org_id)
        if users and user_id in users:
            users.remove(user_id)
            if not users:
                del _ORG_USERS[org_id]
    return True


def fetch_org_settings(org_id: str) -> Dict[str, Any]:
    if not org_id:
        raise ValueError("org_id required")
    with _LOCK:
        return dict(_ORG_SETTINGS.get(org_id, {}))


def update_org_settings(org_id: str, settings: Dict[str, Any]) -> bool:
    if not org_id or not isinstance(settings, dict):
        raise ValueError("org_id and settings required")
    with _LOCK:
        _ORG_SETTINGS[org_id] = dict(settings)
    return True


# ========== SEMANTIC SEARCH: Evil Placeholder ==========
def semantic_search_df(df, query: str, top_k: int = 5, model=None) -> list:
    raise NotImplementedError("semantic_search_df is not implemented yet.")


# ========== DATAFRAME SUMMARY: Evil Placeholder ==========
def summarize_dataframe(df) -> tuple:
    summary = {
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "memory_MB": round(df.memory_usage(deep=True).sum() / (1024**2), 2),
        "describe": df.describe(include="all").to_dict(),
    }
    return df, summary


# ========== USER PROFILE FETCH/SAVE ==========
def fetch_user_profile(
    user_id: str, token: Optional[str] = None, org: Optional[str] = None
) -> Dict[str, Any]:
    if not user_id:
        raise ValueError("user_id required")
    try:
        return api_get(f"users/{user_id}/profile", token=token, org=org)
    except RuntimeError as ex:
        if "404" in str(ex):
            return {}
        return {"error": str(ex), "success": False, "result": None}
    except Exception as ex:
        return {"error": str(ex), "success": False, "result": None}


def save_user_profile(
    user_id: str,
    profile: Dict[str, Any],
    token: Optional[str] = None,
    org: Optional[str] = None,
) -> Dict[str, Any]:
    if not user_id or not isinstance(profile, dict):
        raise ValueError("user_id and profile dict required")
    try:
        return api_put(f"users/{user_id}/profile", data=profile, token=token, org=org)
    except Exception as ex:
        return {"error": str(ex), "success": False, "result": None}


# ====== KNOWLEDGE GRAPH ======
def fetch_knowledge_graph(user_id: str = None, query: str = "") -> dict:
    return {
        "nodes": [{"id": 1, "label": "AI"}, {"id": 2, "label": "World"}],
        "edges": [{"source": 1, "target": 2, "relation": "rules"}],
        "query": query,
    }


def fetch_system_status() -> Dict[str, Any]:
    """Return backend health data or a fallback."""
    try:
        return api_get("health")
    except Exception:
        return {"status": "unknown", "plugins": []}

# ====== PLUGINS ======

def fetch_user_workflows(
    token: Optional[str] = None, org: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Return workflows for the authenticated user or ``[]`` by default."""
    try:
        return api_get("workflows", token=token, org=org)
    except Exception:
        return []


def create_workflow(
    user_id: str,
    workflow: Dict[str, Any],
    token: Optional[str] = None,
    org: Optional[str] = None,
) -> bool:
    """Create a new workflow for ``user_id`` or ``False`` if unavailable."""
    try:
        api_post(
            f"plugins/user_workflows/{user_id}",
            data=workflow,
            token=token,
            org=org,
        )
        return True
    except Exception:
        return False


def delete_workflow(
    user_id: str,
    workflow_id: str,
    token: Optional[str] = None,
    org: Optional[str] = None,
) -> bool:
    """Delete a workflow by id or return ``False`` if unavailable."""
    try:
        api_delete(
            f"plugins/user_workflows/{user_id}/{workflow_id}",
            token=token,
            org=org,
        )
        return True
    except Exception:
        return False


def update_workflow(
    user_id: str,
    workflow_id: str,
    updates: Dict[str, Any],
    token: Optional[str] = None,
    org: Optional[str] = None,
) -> bool:
    """Update an existing workflow or ``False`` if unavailable."""
    try:
        api_put(
            f"plugins/user_workflows/{user_id}/{workflow_id}",
            data=updates,
            token=token,
            org=org,
        )
        return True
    except Exception:
        return False
      


def list_plugins() -> list:
    """Return available plugins."""
    return ["evil_plugin", "super_plugin"]


def install_plugin(plugin_name: str) -> bool:
    """Install a plugin."""
    return True


def uninstall_plugin(plugin_name: str) -> bool:
    """Uninstall a plugin."""
    return True


def enable_plugin(plugin_name: str) -> bool:
    """Enable a plugin."""
    return True


def disable_plugin(plugin_name: str) -> bool:
    """Disable a plugin."""
    return True




# ========================= MEMORY ANALYTICS =========================


def fetch_memory_metrics(
    start_date: Optional[datetime.datetime] = None,
    end_date: Optional[datetime.datetime] = None,
    session_id: Optional[str] = None,
    metric_type: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 500,
    token: Optional[str] = None,
    org: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch memory metrics from the backend API for analytics.
    Args:
        start_date, end_date: datetime (UTC) window for query.
        session_id: Filter for specific session.
        metric_type: Recall, Write, Decay, Miss, etc.
        user_id: Target user.
        limit: Max rows.
    Returns:
        List of metrics (dicts).
    """
    params = {"limit": limit}
    if start_date:
        params["start_date"] = start_date.isoformat()
    if end_date:
        params["end_date"] = end_date.isoformat()
    if session_id:
        params["session_id"] = session_id
    if metric_type:
        params["metric_type"] = metric_type
    if user_id:
        params["user_id"] = user_id
    return api_get("memory/metrics", params=params, token=token, org=org)


def fetch_memory_analytics(
    user_id: Optional[str] = None,
    limit: int = 100,
    token: Optional[str] = None,
    org: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetch memory analytics summary for a user.
    Args:
        user_id: Which user to fetch for.
        limit: How many records.
    Returns:
        Dict of analytics (summary, breakdown, etc).
    """
    params = {"limit": limit}
    if user_id:
        params["user_id"] = user_id
    return api_get("memory/analytics", params=params, token=token, org=org)


def fetch_session_memory(
    session_id: str = None,
    user_id: Optional[str] = None,
    limit: int = 500,
    start_date: Optional[datetime.datetime] = None,
    end_date: Optional[datetime.datetime] = None,
    token: Optional[str] = None,
    org: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch memory records for a specific session (or user) from the backend API.
    Args:
        session_id: Session ID string (required for session view).
        user_id: Optional user filter.
        limit: Maximum number of memory entries.
        start_date, end_date: Optional datetime filters (UTC).
        token, org: RBAC / multi-tenant context.
    Returns:
        List of memory entries (dicts), empty list if none.
    """
    if not session_id and not user_id:
        raise ValueError("At least session_id or user_id must be provided.")

    params = {"limit": limit}
    if session_id:
        params["session_id"] = session_id
    if user_id:
        params["user_id"] = user_id
    if start_date:
        params["start_date"] = start_date.isoformat()
    if end_date:
        params["end_date"] = end_date.isoformat()
    try:
        return api_get("memory/session", params=params, token=token, org=org)
    except Exception:
        # Standardize the error structure for UI consumers
        return []


__all__ = [
    # HTTP API
    "api_get",
    "api_post",
    "api_put",
    "api_delete",
    "fetch_audit_logs",
    "fetch_announcements",
    "api_plugin_action",
    "api_health",
    "api_list_plugins",
    "api_upload_file",
    "ping_services",
    # RBAC/Admin
    "fetch_user_roles",
    "update_user_roles",
    "fetch_role_policies",
    "update_role_policies",
    "add_role_to_user",
    "remove_role_from_user",
    "add_policy_to_role",
    "remove_policy_from_role",
    "list_all_roles",
    "list_all_users",
    "fetch_org_users",
    "add_org_user",
    "update_org_user",
    "remove_org_user",
    "fetch_org_settings",
    "update_org_settings",
    # Data search/summary
    "semantic_search_df",
    "summarize_dataframe",
    "fetch_user_profile",
    "save_user_profile",
    "fetch_knowledge_graph",
    "fetch_system_status",
    # Plugins
    "fetch_user_workflows",
    "create_workflow",
    "delete_workflow",
    "update_workflow",
    "list_plugins",
    "install_plugin",
    "uninstall_plugin",
    "enable_plugin",
    "disable_plugin",
    "fetch_memory_metrics",
    "fetch_memory_analytics",
    "fetch_session_memory",
]
