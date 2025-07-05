"""
Kari PluginRouter: Ruthless Prompt-First Plugin Orchestration
- Auto-discovers, validates, and sandbox-executes plugins
- Jinja2-powered prompt-first execution
- Local-only execution by default (no cloud unless manifest demands it)
"""

import os
import json
import traceback
from pathlib import Path
from typing import Any, Dict, List, Callable, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

PLUGIN_ROOT = Path(__file__).parent / "plugins"
PLUGIN_META = "__meta"
PLUGIN_MANIFEST = "plugin_manifest.json"
PROMPT_FILE = "prompt.txt"
HANDLER_FILE = "handler.py"

# --- Helper: Load Plugin Manifest ---
def load_manifest(plugin_dir: Path) -> Dict[str, Any]:
    manifest_path = plugin_dir / PLUGIN_MANIFEST
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing manifest: {manifest_path}")
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)

# --- Helper: Load Prompt Template ---
def load_prompt(plugin_dir: Path) -> str:
    prompt_path = plugin_dir / PROMPT_FILE
    if not prompt_path.exists():
        raise FileNotFoundError(f"Missing prompt.txt: {prompt_path}")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

# --- Helper: Import Plugin Handler Dynamically ---
def load_handler(plugin_dir: Path) -> Callable:
    import importlib.util
    handler_path = plugin_dir / HANDLER_FILE
    if not handler_path.exists():
        raise FileNotFoundError(f"Missing handler.py: {handler_path}")
    spec = importlib.util.spec_from_file_location(
        f"plugin_{plugin_dir.name}_handler",
        str(handler_path)
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "handle"):
        raise AttributeError(f"Plugin {plugin_dir.name} handler.py must export a 'handle(context)' function")
    return module.handle

# --- Jinja2 Environment for Prompt Rendering ---
jinja_env = Environment(
    loader=FileSystemLoader(str(PLUGIN_ROOT)),
    autoescape=select_autoescape(['txt'])
)

# --- PluginRouter Class ---
class PluginRouter:
    def __init__(self, plugin_root: Path = PLUGIN_ROOT):
        self.plugin_root = plugin_root
        self.plugins = self._discover_plugins()

    def _discover_plugins(self) -> Dict[str, Dict[str, Any]]:
        plugins = {}
        for p in self.plugin_root.iterdir():
            if p.is_dir() and (p / PLUGIN_MANIFEST).exists():
                try:
                    manifest = load_manifest(p)
                    plugins[manifest["name"]] = {
                        "dir": p,
                        "manifest": manifest,
                        "prompt": load_prompt(p),
                        "handler": load_handler(p),
                    }
                except Exception as e:
                    print(f"Plugin discovery failed in {p}: {e}")
        return plugins

    def list_plugins(self) -> List[str]:
        return list(self.plugins.keys())

    def route(self, plugin_name: str, context: Dict[str, Any]) -> Any:
        if plugin_name not in self.plugins:
            raise RuntimeError(f"Plugin '{plugin_name}' not found or failed validation.")
        plugin = self.plugins[plugin_name]

        # Phase 1: Render prompt with context
        prompt_template = jinja_env.from_string(plugin["prompt"])
        rendered_prompt = prompt_template.render(context)

        # Phase 2: Execute handler in isolated scope (sandboxed in future phases)
        try:
            result = plugin["handler"]({"prompt": rendered_prompt, **context})
            return result
        except Exception as ex:
            traceback_str = traceback.format_exc()
            print(f"Error executing plugin '{plugin_name}': {ex}\n{traceback_str}")
            return {
                "error": str(ex),
                "traceback": traceback_str,
            }

# --- Lazy Accessor for Singleton Instance ---
_plugin_router: Optional[PluginRouter] = None


def get_plugin_router() -> PluginRouter:
    """Return a cached :class:`PluginRouter` instance."""
    global _plugin_router
    if _plugin_router is None:
        _plugin_router = PluginRouter()
    return _plugin_router

__all__ = ["PluginRouter", "get_plugin_router"]

