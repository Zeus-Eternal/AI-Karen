"""
Kari PluginRouter: Ruthless Prompt‐First Plugin Orchestration
- Auto‐discovers, validates, and sandbox‐executes plugins
- Jinja2‐powered prompt‐first execution
- Local‐only execution by default (no cloud unless manifest demands it)
"""

import os
import json
import inspect
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# --- Prometheus metrics (optional) -------------------------------------
try:
    from prometheus_client import Counter, REGISTRY

    # avoid double‐registration on reload
    if "plugin_import_error_total" not in REGISTRY._names_to_collectors:
        PLUGIN_IMPORT_ERRORS = Counter(
            "plugin_import_error_total",
            "Plugin import failures",
            ["plugin", "module", "error"],
        )
    else:
        PLUGIN_IMPORT_ERRORS = REGISTRY._names_to_collectors["plugin_import_error_total"]
except ImportError:
    class _DummyMetric:
        def labels(self, **kw): return self
        def inc(self, n: int = 1): pass
    PLUGIN_IMPORT_ERRORS = _DummyMetric()


# --- Sandboxing helper --------------------------------------------------
from ai_karen_engine.utils.sandbox import run_in_sandbox  # your existing sandbox runner


# --- Jinja2 environment (optional) -------------------------------------
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    jinja_env = Environment(
        loader=FileSystemLoader(str(Path(__file__).parent.parent.parent.parent / "plugins")),
        autoescape=select_autoescape(['txt'])
    )
except ImportError:
    # fallback to simple str.format
    class Environment:
        def __init__(self, *args, **kw): pass
        def from_string(self, text):
            class T:
                def __init__(self, t): self.t = t
                def render(self, ctx): return self.t.format(**ctx)
            return T(text)
    jinja_env = Environment()


# --- Paths & schema -----------------------------------------------------
# Plugin root now points to the root plugins directory (marketplace structure)
PLUGIN_ROOT       = Path(__file__).parent.parent.parent.parent / "plugins"
PLUGIN_META       = "__meta"
PLUGIN_MANIFEST   = "plugin_manifest.json"
PROMPT_FILE       = "prompt.txt"
HANDLER_FILE      = "handler.py"
SCHEMA_PATH       = Path(__file__).parents[1] / "config" / "plugin_schema.json"


def load_schema() -> Dict[str, Any]:
    try:
        return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def validate_manifest(manifest: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    # If jsonschema is installed, use it; else fallback to key check
    try:
        import jsonschema  # type: ignore
        jsonschema.validate(instance=manifest, schema=schema)
        return True
    except Exception:
        required = schema.get(
            "required",
            ["plugin_api_version", "intent", "required_roles", "trusted_ui"]
        )
        return all(k in manifest for k in required)


def load_manifest(plugin_dir: Path) -> Dict[str, Any]:
    mf = plugin_dir / PLUGIN_MANIFEST
    if not mf.exists():
        raise FileNotFoundError(f"Missing manifest: {mf}")
    return json.loads(mf.read_text(encoding="utf-8"))


def load_prompt(plugin_dir: Path) -> str:
    pf = plugin_dir / PROMPT_FILE
    if not pf.exists():
        raise FileNotFoundError(f"Missing prompt.txt: {pf}")
    return pf.read_text(encoding="utf-8")


def load_handler(plugin_dir: Path, module_path: Optional[str] = None) -> Tuple[Callable, str]:
    """
    Return (handler_callable, module_name).
    Handler must expose `async def run(params)` or `def run(params)`.
    """
    import importlib
    import importlib.util

    if module_path:
        module = importlib.import_module(module_path)
    else:
        handler_py = plugin_dir / HANDLER_FILE
        if not handler_py.exists():
            raise FileNotFoundError(f"Missing handler.py: {handler_py}")
        spec = importlib.util.spec_from_file_location(f"plugin_{plugin_dir.name}", str(handler_py))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore

    if not hasattr(module, "run"):
        raise AttributeError(f"Plugin '{plugin_dir.name}' handler must define `run(params)`")
    return getattr(module, "run"), module.__name__


# --- Plugin record & router --------------------------------------------
class AccessDenied(Exception):
    """User lacks required roles for this plugin."""
    pass


class PluginRecord:
    def __init__(
        self,
        manifest: Dict[str, Any],
        handler: Callable,
        module_name: str,
        ui: Optional[Callable],
        dir_path: Path
    ):
        self.manifest    = manifest
        self.handler     = handler
        self.module_name = module_name
        self.ui          = ui
        self.dir_path    = dir_path


class PluginRouter:
    def __init__(self, plugin_root: Path = PLUGIN_ROOT):
        self.plugin_root = plugin_root
        self.schema      = load_schema()
        self.intent_map: Dict[str, PluginRecord] = {}
        self.reload()

    def _discover_plugins(self) -> Dict[str, PluginRecord]:
        out: Dict[str, PluginRecord] = {}
        self._scan_directory_for_plugins(self.plugin_root, out)
        return out
    
    def _scan_directory_for_plugins(self, directory: Path, out: Dict[str, PluginRecord]) -> None:
        """
        Recursively scan directory for plugins, supporting categorized structure.
        """
        for p in directory.iterdir():
            if not p.is_dir():
                continue
                
            # Skip metadata directories
            if p.name.startswith('__') or p.name.startswith('.'):
                continue
            
            mf = p / PLUGIN_MANIFEST
            if mf.exists():
                # Found a plugin directory with manifest
                try:
                    manifest = load_manifest(p)
                    if not validate_manifest(manifest, self.schema):
                        raise ValueError("Invalid manifest schema")

                    handler, mod_name = load_handler(p, manifest.get("module"))
                    ui = None
                    ui_py = p / "ui.py"
                    if ui_py.exists() and (os.getenv("ADVANCED_MODE") or manifest.get("trusted_ui")):
                        import importlib.util
                        spec = importlib.util.spec_from_file_location(f"plugin_ui_{p.name}", str(ui_py))
                        ui_mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(ui_mod)  # type: ignore
                        ui = getattr(ui_mod, "render", None)

                    intents = manifest.get("intent") or []
                    if isinstance(intents, str):
                        intents = [intents]
                    for intent in intents:
                        out[intent] = PluginRecord(manifest, handler, mod_name, ui, p)

                except Exception as e:
                    # increment import‐error metric (labels auto‐noop if disabled)
                    PLUGIN_IMPORT_ERRORS.labels(
                        plugin=p.name,
                        module=manifest.get("module", HANDLER_FILE) if 'manifest' in locals() else HANDLER_FILE,
                        error=type(e).__name__
                    ).inc()
                    print(f"Plugin discovery failed in {p}: {e}")
            else:
                # No manifest here, scan subdirectories (for category structure)
                self._scan_directory_for_plugins(p, out)

    def reload(self) -> None:
        # reconfigure Jinja loader in case plugins folder changed
        try:
            jinja_env.loader = FileSystemLoader(str(self.plugin_root))
        except NameError:
            pass
        self.intent_map = self._discover_plugins()

    def list_intents(self) -> List[str]:
        return list(self.intent_map)
    
    def get_plugin(self, intent: str) -> Optional[PluginRecord]:
        """Get plugin record for a specific intent."""
        return self.intent_map.get(intent)

    def get_handler(self, intent: str) -> Optional[Callable]:
        rec = self.get_plugin(intent)
        return rec.handler if rec else None

    async def dispatch(
        self,
        intent: str,
        params: Dict[str, Any],
        roles: Optional[List[str]] = None
    ) -> Any:
        rec = self.get_plugin(intent)
        if not rec:
            raise RuntimeError(f"No plugin for intent '{intent}'")

        # enforce RBAC
        required = rec.manifest.get("required_roles", [])
        if required and not (roles and set(roles).intersection(required)):
            raise AccessDenied(f"Intent '{intent}' requires one of {required}")

        # render prompt
        template = jinja_env.from_string(rec.manifest.get("prompt", "{{prompt}}"))
        rendered = template.render(params)

        # prepare payload
        payload = {"prompt": rendered, **params}

        # execute in sandbox or direct
        if rec.manifest.get("sandbox", True):
            # run_in_sandbox returns awaitable result
            return await run_in_sandbox(rec.handler, payload)
        else:
            result = rec.handler(payload)
            if inspect.iscoroutine(result):
                return await result
            return result


# --- Singleton accessor -------------------------------------------------
_plugin_router: Optional[PluginRouter] = None

def get_plugin_router() -> PluginRouter:
    global _plugin_router
    if _plugin_router is None:
        _plugin_router = PluginRouter()
    return _plugin_router


__all__ = [
    "PluginRouter",
    "get_plugin_router",
    "AccessDenied",
    "PluginRecord",
    "PLUGIN_IMPORT_ERRORS",
]
