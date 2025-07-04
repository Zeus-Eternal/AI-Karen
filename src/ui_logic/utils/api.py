"""
Kari UI Universal API Utility
- Centralized fetcher for all UI layers (mobile, desktop, admin)
- Handles RBAC tokens, error translation, observability
- Enterprise-grade: handles multi-tenant, plugin, and fallback local APIs
"""

import requests
from typing import Any, Dict, Optional, Union
import logging
import os

API_BASE = os.getenv("KARI_API_BASE", "http://localhost:8000/api")
TIMEOUT = float(os.getenv("KARI_API_TIMEOUT", "30"))

logger = logging.getLogger("kari.ui.api")
logger.setLevel(logging.INFO)

def get_auth_headers(token: Optional[str] = None, org: Optional[str] = None) -> Dict[str, str]:
    """Inject RBAC and org context headers for all API calls."""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if org:
        headers["X-Org-ID"] = org
    return headers

def handle_response(resp: requests.Response) -> Any:
    """Uniform response/error handler."""
    try:
        resp.raise_for_status()
        if "application/json" in resp.headers.get("Content-Type", ""):
            return resp.json()
        return resp.text
    except requests.HTTPError as e:
        logger.error(f"API error: {e.response.status_code} {e.response.text}")
        raise RuntimeError(f"API error: {e.response.status_code} {e.response.text}")

def api_get(
    path: str,
    params: Optional[Dict[str, Any]] = None,
    token: Optional[str] = None,
    org: Optional[str] = None,
    timeout: Optional[float] = None
) -> Any:
    url = f"{API_BASE.rstrip('/')}/{path.lstrip('/')}"
    headers = get_auth_headers(token, org)
    resp = requests.get(url, headers=headers, params=params, timeout=timeout or TIMEOUT)
    return handle_response(resp)

def api_post(
    path: str,
    data: Optional[Union[Dict, str]] = None,
    token: Optional[str] = None,
    org: Optional[str] = None,
    timeout: Optional[float] = None,
    json: bool = True,
    files: Optional[Dict] = None
) -> Any:
    url = f"{API_BASE.rstrip('/')}/{path.lstrip('/')}"
    headers = get_auth_headers(token, org)
    if files:
        resp = requests.post(url, headers=headers, files=files, data=data, timeout=timeout or TIMEOUT)
    else:
        if json:
            resp = requests.post(url, headers=headers, json=data, timeout=timeout or TIMEOUT)
        else:
            resp = requests.post(url, headers=headers, data=data, timeout=timeout or TIMEOUT)
    return handle_response(resp)

def api_put(
    path: str,
    data: Optional[Union[Dict, str]] = None,
    token: Optional[str] = None,
    org: Optional[str] = None,
    timeout: Optional[float] = None,
    json: bool = True
) -> Any:
    url = f"{API_BASE.rstrip('/')}/{path.lstrip('/')}"
    headers = get_auth_headers(token, org)
    if json:
        resp = requests.put(url, headers=headers, json=data, timeout=timeout or TIMEOUT)
    else:
        resp = requests.put(url, headers=headers, data=data, timeout=timeout or TIMEOUT)
    return handle_response(resp)

def api_delete(
    path: str,
    token: Optional[str] = None,
    org: Optional[str] = None,
    timeout: Optional[float] = None
) -> Any:
    url = f"{API_BASE.rstrip('/')}/{path.lstrip('/')}"
    headers = get_auth_headers(token, org)
    resp = requests.delete(url, headers=headers, timeout=timeout or TIMEOUT)
    return handle_response(resp)

# --- Advanced Patterns: Plugin, Health, Multi-Tenant ---
def api_plugin_action(plugin: str, action: str, payload: Optional[dict] = None, token: Optional[str] = None, org: Optional[str] = None) -> Any:
    """Call a plugin endpoint safely from the UI."""
    return api_post(f"plugins/{plugin}/{action}", data=payload, token=token, org=org)

def api_health(token: Optional[str] = None) -> Any:
    """Fetch system health/status."""
    return api_get("health", token=token)

def api_list_plugins(token: Optional[str] = None, org: Optional[str] = None) -> Any:
    return api_get("plugins", token=token, org=org)

def api_upload_file(path: str, file_path: str, token: Optional[str] = None, org: Optional[str] = None) -> Any:
    """Upload a file from the UI to API."""
    with open(file_path, "rb") as f:
        files = {"file": f}
        return api_post(path, files=files, token=token, org=org, json=False)

# --- Usage Example (for dev/test) ---
if __name__ == "__main__":
    # Example: test API health
    print(api_health())
