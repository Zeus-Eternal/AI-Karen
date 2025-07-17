import os
import sys
import importlib
import logging
import traceback
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

try:
    import streamlit as st
except Exception:  # pragma: no cover - optional dependency
    class _Dummy:
        def __getattr__(self, name):
            return self

        def __call__(self, *args, **kwargs):
            return None

    st = _Dummy()
from ui_logic.hooks.rbac import require_roles
from ui_logic.utils.api import (
    list_plugins,
    install_plugin,
    uninstall_plugin,
    enable_plugin,
    disable_plugin,
    fetch_audit_logs,
)

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins"

DEFAULT_PLUGIN_SCHEMA = {
    "name": str,
    "description": str,
    "version": str,
    "prompt_file": str,
    "handler_file": str,
    "enabled": bool,
    "rbac": dict,
}

class PluginManagerError(Exception):
    pass

class PluginManifestError(PluginManagerError):
    pass

class PluginValidationError(PluginManagerError):
    pass

class PluginRBACError(PluginManagerError):
    pass

class PluginAuditLogger(logging.LoggerAdapter):
    """Plugin-level audit logger with auto-correlation ID."""
    def process(self, msg, kwargs):
        cid = kwargs.pop("correlation_id", None)
        prefix = f"[cid={cid}] " if cid else ""
        return prefix + msg, kwargs

class PluginManager:
    def __init__(
        self,
        plugin_dir: Optional[Path] = None,
        logger: Optional[logging.Logger] = None,
        metrics_collector: Optional[Callable[[str, dict], None]] = None,
    ):
        self.plugin_dir = Path(plugin_dir or PLUGIN_DIR)
        self.logger = PluginAuditLogger(
            logger or logging.getLogger("kari.plugins"),
            extra={}
        )
        self.metrics = metrics_collector or (lambda event, meta: None)
        self.plugins: Dict[str, dict] = {}
        self.enabled_plugins: Dict[str, dict] = {}
        self._load_plugins()

    def _validate_manifest(self, manifest: dict, plugin_path: Path) -> dict:
        for key, typ in DEFAULT_PLUGIN_SCHEMA.items():
            if key not in manifest:
                raise PluginManifestError(f"{plugin_path}: Missing manifest key: {key}")
            if not isinstance(manifest[key], typ):
                raise PluginManifestError(f"{plugin_path}: Manifest key '{key}' wrong type: expected {typ.__name__}")
        return manifest

    def _discover_plugins(self) -> List[Path]:
        if not self.plugin_dir.exists():
            self.logger.warning(f"Plugin directory {self.plugin_dir} does not exist")
            return []
        return [
            d for d in self.plugin_dir.iterdir()
            if d.is_dir() and (d / "plugin_manifest.json").exists()
        ]

    def _load_plugins(self):
        self.plugins.clear()
        self.enabled_plugins.clear()
        for pdir in self._discover_plugins():
            manifest = {}
            try:
                with open(pdir / "plugin_manifest.json", "r") as f:
                    manifest = json.load(f)
                self._validate_manifest(manifest, pdir)
                plugin = {
                    "manifest": manifest,
                    "path": pdir,
                    "prompt": (pdir / manifest["prompt_file"]).read_text(encoding="utf-8"),
                    "handler": None,
                    "enabled": manifest.get("enabled", True)
                }
                if not self._validate_rbac(plugin):
                    raise PluginRBACError(f"{manifest['name']}: RBAC check failed.")
                handler_file = pdir / manifest["handler_file"]
                if handler_file.exists():
                    sys.path.insert(0, str(pdir))
                    plugin_module = importlib.import_module(handler_file.stem)
                    sys.path.pop(0)
                    plugin["handler"] = plugin_module
                self.plugins[manifest["name"]] = plugin
                if plugin["enabled"]:
                    self.enabled_plugins[manifest["name"]] = plugin
                self.logger.info(f"Loaded plugin: {manifest['name']}")
            except Exception as ex:
                self.logger.error(
                    f"Plugin load failed in {pdir}: {ex}\n{traceback.format_exc()}",
                    extra={"correlation_id": manifest.get("name", str(pdir))}
                )
                self.metrics("plugin_load_failed", {"plugin": str(pdir), "error": str(ex)})

    def _validate_rbac(self, plugin: dict) -> bool:
        return True

    def reload_plugins(self):
        self.logger.info("Reloading plugins (hot-reload)")
        self._load_plugins()

    def get_enabled_plugins(self) -> List[str]:
        return list(self.enabled_plugins.keys())

    def get_plugin(self, name: str) -> dict:
        if name not in self.plugins:
            raise PluginManagerError(f"Plugin '{name}' not found")
        return self.plugins[name]

    def execute_plugin(self, name: str, input_data: dict, context: Optional[dict] = None) -> Any:
        if name not in self.enabled_plugins:
            raise PluginManagerError(f"Plugin '{name}' is not enabled or missing")
        plugin = self.enabled_plugins[name]
        handler = plugin.get("handler")
        prompt = plugin["prompt"]
        try:
            if handler and hasattr(handler, "run"):
                result = handler.run(prompt=prompt, input_data=input_data, context=context or {})
                self.metrics("plugin_exec_success", {"plugin": name})
                return result
            filled = prompt.format(**input_data)
            self.metrics("plugin_exec_prompt", {"plugin": name})
            return filled
        except Exception as ex:
            self.logger.error(
                f"Plugin execution failed [{name}]: {ex}\n{traceback.format_exc()}",
                extra={"correlation_id": name}
            )
            self.metrics("plugin_exec_failed", {"plugin": name, "error": str(ex)})
            raise PluginManagerError(f"Plugin execution failed: {ex}")

    def enable_plugin(self, name: str):
        if name not in self.plugins:
            raise PluginManagerError(f"Plugin '{name}' not found")
        self.plugins[name]["enabled"] = True
        self.enabled_plugins[name] = self.plugins[name]
        self.logger.info(f"Plugin enabled: {name}")
        self.metrics("plugin_enabled", {"plugin": name})

    def disable_plugin(self, name: str):
        if name not in self.plugins:
            raise PluginManagerError(f"Plugin '{name}' not found")
        self.plugins[name]["enabled"] = False
        self.enabled_plugins.pop(name, None)
        self.logger.info(f"Plugin disabled: {name}")
        self.metrics("plugin_disabled", {"plugin": name})

    def list_all_plugins(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": meta["manifest"]["name"],
                "description": meta["manifest"].get("description"),
                "version": meta["manifest"].get("version"),
                "enabled": meta.get("enabled"),
                "rbac": meta["manifest"].get("rbac", {}),
                "path": str(meta["path"])
            }
            for meta in self.plugins.values()
        ]

    def audit_log(self, event: str, data: dict):
        self.logger.info(f"[audit] {event} | {data}")

# ---- UI Component ----
def render_plugin_manager(user_ctx: dict):
    """Render the Streamlit UI for plugin management."""
    if not require_roles(user_ctx, ["admin", "developer"]):
        st.error("Insufficient privileges to view plugin manager.")
        return

    st.header("Kari Plugin Manager")
    st.sidebar.button("Reload Plugins", on_click=lambda: st.experimental_rerun())

    plugins = list_plugins(user_ctx["user_id"])
    for plugin in plugins:
        name = plugin["name"]
        enabled = plugin.get("enabled", False)
        st.subheader(name)
        st.write(plugin.get("description", "No description"))
        col1, col2 = st.columns([1, 1])
        if col1.checkbox("Enabled", enabled, key=f"en_{name}") != enabled:
            set_plugin_enabled = enable_plugin if not enabled else disable_plugin
            success = set_plugin_enabled(user_ctx["user_id"], name)
            if success:
                st.success(f"Plugin '{name}' {'enabled' if not enabled else 'disabled'}.")
        if col2.button("Uninstall", key=f"un_{name}"):
            if uninstall_plugin(user_ctx["user_id"], name):
                st.warning(f"Plugin '{name}' uninstalled.")
    
    st.markdown("---")
    st.subheader("Audit Trail")
    logs = fetch_audit_logs(category="plugin", user_id=user_ctx["user_id"])[-25:][::-1]
    for entry in logs:
        st.text(f"{entry['timestamp']} - {entry['event']} - {entry['data']}")

__all__ = [
    "PluginManager",
    "PluginManagerError",
    "PluginManifestError",
    "PluginValidationError",
    "PluginRBACError",
    "create_plugin_manager",
    "render_plugin_manager",
]
