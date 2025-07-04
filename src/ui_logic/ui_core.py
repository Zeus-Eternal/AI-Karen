"""
Kari UI Core Logic
- Builds page manifests and dispatches page handlers
- RBAC and feature flag guarded
"""

from typing import Any, Dict, Callable, List
import logging

from src.ui_logic.config.pages_manifest import PAGES
from src.ui_logic.config.feature_flags import get_flag
from src.ui_logic.hooks.rbac import check_rbac

# --- Page Handler Registry ---
from src.ui_logic.pages import plugin_manager as plugin_manager_page

PAGE_HANDLERS: Dict[str, Callable[[Dict[str, Any]], Any]] = {
    "plugin_manager": plugin_manager_page.plugin_manager_page,
}


def get_page_manifest(user_ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return manifest of pages accessible to the current user."""
    manifest: List[Dict[str, Any]] = []
    for entry in PAGES:
        flag = entry.get("flag")
        if flag and not get_flag(flag):
            continue
        if not check_rbac(user_ctx, entry.get("roles", [])):
            continue
        manifest.append(entry)
    return manifest


def dispatch_page(page_key: str, user_ctx: Dict[str, Any], **kwargs: Any) -> Any:
    """Dispatch to the registered page handler after RBAC/flag checks."""
    entry = next((p for p in PAGES if p["key"] == page_key), None)
    if not entry:
        raise KeyError(f"Page {page_key} not registered")
    if entry.get("flag") and not get_flag(entry["flag"]):
        raise PermissionError("Feature flag disabled for page")
    if not check_rbac(user_ctx, entry.get("roles", [])):
        raise PermissionError("Access denied for page")
    handler = PAGE_HANDLERS.get(page_key)
    if not handler:
        raise NotImplementedError(f"Handler for {page_key} not implemented")
    logging.info("Dispatching page %s for user %s", page_key, user_ctx.get("user_id"))
    return handler(user_ctx=user_ctx, **kwargs)


if __name__ == "__main__":
    demo_ctx = {"user_id": "zeus", "roles": ["admin", "developer"]}
    print(get_page_manifest(demo_ctx))
    try:
        dispatch_page("plugin_manager", demo_ctx)
    except NotImplementedError:
        print("Dispatch works: plugin manager not yet implemented")
