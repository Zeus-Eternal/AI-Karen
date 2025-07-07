"""UI Core Logic Module

Provides minimal page dispatch and manifest retrieval for Kari UI.
All logic here is framework-agnostic and enforces feature flag gating
and RBAC checks before any page handler is executed.

Security notes:
- Do not import UI frameworks directly in this layer.
- Never bypass feature flag or RBAC checks when dispatching pages.
"""

from importlib import import_module
from typing import Any, Callable, Dict, List, Optional

from src.ui_logic.config import pages_manifest
from src.ui_logic.config.feature_flags import get_flag
from src.ui_logic.hooks.rbac import check_rbac


def get_page_manifest(user_ctx: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Return allowed pages for ``user_ctx`` filtered by feature flags and RBAC."""
    allowed: List[Dict[str, Any]] = []
    for page in pages_manifest.PAGES:
        flag = page.get("feature_flag")
        if flag and not get_flag(flag):
            continue
        roles = page.get("required_roles", [])
        if roles and not check_rbac(user_ctx, roles):
            continue
        allowed.append(page)
    return allowed


def dispatch_page(
    page_key: str,
    user_ctx: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> Callable[..., Any]:
    """Load the module for ``page_key`` and return its page handler."""
    entry = next((p for p in pages_manifest.PAGES if p.get("route") == page_key), None)
    if entry is None:
        raise KeyError(f"Unknown page '{page_key}'")

    flag = entry.get("feature_flag")
    if flag and not get_flag(flag):
        raise PermissionError(f"Feature disabled for page '{page_key}'")

    roles = entry.get("required_roles", [])
    if roles and not check_rbac(user_ctx, roles):
        raise PermissionError(f"Access denied to '{page_key}'")

    module_path = entry.get("import")
    try:
        module = import_module(module_path)
    except Exception as exc:  # noqa: BLE001
        raise ImportError(f"Could not import page module '{module_path}'") from exc

    handler = (
        getattr(module, f"{page_key}_page", None)
        or getattr(module, "render_page", None)
        or getattr(module, f"get_{page_key}_page", None)
    )
    if handler is None or not callable(handler):
        raise AttributeError(f"No handler callable found for page '{page_key}'")

    return handler


if __name__ == "__main__":
    pages = get_page_manifest({"roles": ["admin", "user"]})
    print("Available pages:", [p["route"] for p in pages])
    if pages:
        handler = dispatch_page(pages[0]["route"], {"roles": ["admin", "user"]})
        print("Loaded handler:", handler)
