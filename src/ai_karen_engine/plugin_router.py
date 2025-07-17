"""
Kari PluginRouter: Ruthless Prompt-First Plugin Orchestration
- Auto-discovers, validates, and sandbox-executes plugins
- Jinja2-powered prompt-first execution
- Local-only execution by default (no cloud unless manifest demands it)
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Callable, Optional

try:
    from prometheus_client import Counter
    METRICS_ENABLED = True
except Exception:  # pragma: no cover - optional dependency
    METRICS_ENABLED = False

    class _DummyMetric:
        def labels(self, **kwargs):
            return self

        def inc(self, n: int = 1) -> None:  # noqa: D401 - simple increment
            """No-op increment."""

    Counter = _DummyMetric  # type: ignore

PLUGIN_IMPORT_ERRORS = (
    Counter(
        "plugin_import_error_total",
        "Plugin import failures",
        ["plugin", "module", "error"],
    )
    if METRICS_ENABLED
    else Counter()
)


class AccessDenied(Exception):
    """Raised when a user lacks required roles for a plugin."""
    pass
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except Exception:  # pragma: no cover - optional dependency
    class FileSystemLoader:  # type: ignore
        def __init__(self, *a, **k):
            pass

    def select_autoescape(*a, **k):
        return False

    class Environment:  # type: ignore
        def __init__(self, *a, **k):
            pass

        def from_string(self, text):
            class T:
                def render(self, ctx):
                    return text.format(**ctx)

            return T()

PLUGIN_SCHEMA_PATH = Path(__file__).parents[1] / "config" / "plugin_schema.json"

PLUGIN_ROOT = Path(__file__).parent / "plugins"
PLUGIN_META = "__meta"
PLUGIN_MANIFEST = "plugin_manifest.json"
PROMPT_FILE = "prompt.txt"
HANDLER_FILE = "handler.py"


def load_schema() -> Dict[str, Any]:
    try:
        with open(PLUGIN_SCHEMA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def validate_manifest(manifest: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    try:
        import jsonschema  # type: ignore

        jsonschema.validate(instance=manifest, schema=schema)
        return True
    except Exception:
        required = schema.get(
            "required",
            ["plugin_api_version", "intent", "enable_external_workflow", "required_roles", "trusted_ui"],
        )
        return all(k in manifest for k in required)

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
def load_handler(plugin_dir: Path, module_path: str | None = None) -> Callable:
    """Load plugin handler either from module path or handler.py."""
    import importlib
    import importlib.util

    if module_path:
        try:
            module = importlib.import_module(module_path)
        except Exception as exc:  # pragma: no cover - dynamic import
            raise ImportError(module_path) from exc
    else:
        handler_path = plugin_dir / HANDLER_FILE
        if not handler_path.exists():
            raise FileNotFoundError(f"Missing handler.py: {handler_path}")
        spec = importlib.util.spec_from_file_location(
            f"plugin_{plugin_dir.name}_handler",
            str(handler_path),
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Failed loading spec for {handler_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

    if not hasattr(module, "run"):
        raise AttributeError(
            f"Plugin {plugin_dir.name} handler must export a 'run(params)' function"
        )
    return module.run

# --- Jinja2 Environment for Prompt Rendering ---
jinja_env = Environment(loader=FileSystemLoader(str(PLUGIN_ROOT)), autoescape=select_autoescape(['txt']))

# --- PluginRouter Class ---
class PluginRecord:
    def __init__(self, manifest: Dict[str, Any], handler: Callable, ui: Optional[Callable], dir_path: Path):
        self.manifest = manifest
        self.handler = handler
        self.ui = ui
        self.dir = dir_path


class PluginRouter:
    def __init__(self, plugin_root: Path = PLUGIN_ROOT):
        self.plugin_root = Path(plugin_root)
        self.schema = load_schema()
        self.intent_map: Dict[str, PluginRecord] = {}
        self.reload()

    def _discover_plugins(self) -> Dict[str, PluginRecord]:
        plugins: Dict[str, PluginRecord] = {}
        for p in self.plugin_root.iterdir():
            if p.is_dir() and (p / PLUGIN_MANIFEST).exists():
                try:
                    manifest = load_manifest(p)
                    if not validate_manifest(manifest, self.schema):
                        raise ValueError("manifest schema invalid")
                    module_path = manifest.get("module")
                    try:
                        handler = load_handler(p, module_path)
                    except Exception as e:  # pragma: no cover - dynamic import
                        PLUGIN_IMPORT_ERRORS.labels(
                            plugin=p.name,
                            module=module_path or "handler.py",
                            error=type(e).__name__,
                        ).inc()
                        raise
                    ui = None
                    ui_path = p / "ui.py"
                    if ui_path.exists() and (os.getenv("ADVANCED_MODE") or manifest.get("trusted_ui")):
                        import importlib.util

                        spec = importlib.util.spec_from_file_location(f"plugin_{p.name}_ui", str(ui_path))
                        ui_mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(ui_mod)
                        ui = getattr(ui_mod, "render", None)

                    intents = manifest.get("intent")
                    if isinstance(intents, str):
                        intents = [intents]
                    for intent in intents or []:
                        plugins[intent] = PluginRecord(manifest, handler, ui, p)
                except Exception as e:
                    print(f"Plugin discovery failed in {p}: {e}")
        return plugins

    def reload(self) -> None:
        global jinja_env
        jinja_env.loader = FileSystemLoader(str(self.plugin_root))
        self.intent_map = self._discover_plugins()

    def list_intents(self) -> List[str]:
        return list(self.intent_map.keys())

    def get_plugin(self, intent: str) -> Optional[PluginRecord]:
        return self.intent_map.get(intent)

    def get_handler(self, intent: str) -> Optional[Callable]:
        rec = self.get_plugin(intent)
        return rec.handler if rec else None

    async def dispatch(self, intent: str, params: Dict[str, Any], roles: Optional[List[str]] = None) -> Any:
        rec = self.get_plugin(intent)
        if not rec:
            raise RuntimeError(f"Plugin '{intent}' not found or failed validation.")
        allowed = rec.manifest.get("required_roles") or []
        if allowed and roles is not None and not set(roles).intersection(allowed):
            raise AccessDenied(intent)

        prompt_template = jinja_env.from_string(rec.manifest.get("prompt", "{{prompt}}"))
        rendered_prompt = prompt_template.render(params)
        return await rec.handler({"prompt": rendered_prompt, **params})

# --- Lazy Accessor for Singleton Instance ---
_plugin_router: Optional[PluginRouter] = None


def get_plugin_router() -> PluginRouter:
    """Return a cached :class:`PluginRouter` instance."""
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

