"""Minimal UI core dispatch logic."""

from importlib import import_module
from typing import Any, Dict, List

from ui_logic.config.feature_flags import get_flag
from ui_logic.config.pages_manifest import PAGES
from ui_logic.hooks.rbac import check_rbac


def _flag_enabled(flag: str | None) -> bool:
    """Return True if the feature flag is enabled."""
    if not flag or flag == "core":
        return True
    return bool(get_flag(f"enable_{flag}"))


def get_page_manifest(user_ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return page manifest filtered by RBAC and feature flags."""
    filtered: List[Dict[str, Any]] = []
    rbac_on = bool(get_flag("enable_rbac"))
    for page in PAGES:
        roles = page.get("roles", [])
        if rbac_on and not check_rbac(user_ctx, roles):
            continue
        if not _flag_enabled(page.get("flag")):
            continue
        filtered.append(page)
    return filtered


def dispatch_page(page_key: str, user_ctx: Dict[str, Any]) -> Any:
    """Dispatch to the page handler after RBAC and feature checks."""
    entry = next((p for p in PAGES if p.get("key") == page_key), None)
    if entry is None:
        raise KeyError(f"Unknown page: {page_key}")

    roles = entry.get("roles", [])
    if bool(get_flag("enable_rbac")) and not check_rbac(user_ctx, roles):
        raise PermissionError(f"Access denied to page: {page_key}")
    if not _flag_enabled(entry.get("flag")):
        raise PermissionError(f"Feature disabled for page: {page_key}")

    module = import_module(f"ui_logic.pages.{page_key}")
    handler_name = f"{page_key}_page"
    if not hasattr(module, handler_name):
        raise AttributeError(f"Handler {handler_name} not found")
    handler = getattr(module, handler_name)
    return handler(user_ctx=user_ctx)


__all__ = ["get_page_manifest", "dispatch_page"]
