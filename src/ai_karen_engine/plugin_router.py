"""
Kari PluginRouter: Ruthless Prompt‐First Plugin Orchestration
- Auto‐discovers, validates, and sandbox‐executes plugins
- Jinja2‐powered prompt‐first execution
- Local‐only execution by default (no cloud unless manifest demands it)
"""

import asyncio
import os
import json
import inspect
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from ai_karen_engine.hooks.hook_mixin import HookMixin
from ai_karen_engine.hooks.hook_types import HookTypes

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
from ai_karen_engine.utils.sandbox import (
    run_in_sandbox,  # your existing sandbox runner
)

logger = logging.getLogger(__name__)


# --- Jinja2 environment (optional) -------------------------------------
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    jinja_env = Environment(
        loader=FileSystemLoader(str(Path(__file__).parent / "plugins")),
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
# Allow overriding plugin directory via ``KARI_PLUGIN_DIR`` to support
# tests and custom deployments.
PLUGIN_ROOT       = Path(os.getenv("KARI_PLUGIN_DIR", Path(__file__).parent / "plugins"))
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


class PluginRouter(HookMixin):
    def __init__(self, plugin_root: Path = PLUGIN_ROOT):
        super().__init__()
        self.plugin_root = plugin_root
        self.schema      = load_schema()
        self.intent_map: Dict[str, PluginRecord] = {}
        self.name = "plugin_router"
        self.reload()

    def _discover_plugins(self) -> Dict[str, PluginRecord]:
        out: Dict[str, PluginRecord] = {}
        for p in self.plugin_root.iterdir():
            mf = p / PLUGIN_MANIFEST
            if not p.is_dir() or not mf.exists():
                continue
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
                logger.warning("Plugin discovery failed in %s: %s", p, e)

        return out

    def reload(self) -> None:
        # reconfigure Jinja loader in case plugins folder changed
        try:
            jinja_env.loader = FileSystemLoader(str(self.plugin_root))
        except NameError:
            pass
        
        old_intents = set(self.intent_map.keys())
        self.intent_map = self._discover_plugins()
        new_intents = set(self.intent_map.keys())
        
        # Trigger hooks for loaded/unloaded plugins
        # Trigger hooks for loaded/unloaded plugins (only if event loop is running)
        try:
            loop = asyncio.get_running_loop()
            for intent in new_intents - old_intents:
                plugin_record = self.intent_map[intent]
                asyncio.create_task(self.trigger_hook_safe(
                    HookTypes.PLUGIN_LOADED,
                    {
                        "plugin_intent": intent,
                        "plugin_manifest": plugin_record.manifest,
                        "plugin_directory": str(plugin_record.dir_path)
                    }
                ))
            
            for intent in old_intents - new_intents:
                asyncio.create_task(self.trigger_hook_safe(
                    HookTypes.PLUGIN_UNLOADED,
                    {
                        "plugin_intent": intent
                    }
                ))
        except RuntimeError:
            # No event loop running, skip hook triggers
            pass

    def list_intents(self) -> List[str]:
        return list(self.intent_map)

    def get_plugin(self, intent: str) -> Optional[PluginRecord]:
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

        # Trigger pre-dispatch hooks
        dispatch_context = {
            "intent": intent,
            "params": params,
            "roles": roles,
            "plugin_manifest": rec.manifest,
            "plugin_directory": str(rec.dir_path),
            "dispatch_id": f"dispatch_{intent}_{id(params)}"
        }
        
        await self.trigger_hook_safe(
            HookTypes.PLUGIN_EXECUTION_START,
            dispatch_context,
            {"roles": roles} if roles else None
        )

        try:
            # render prompt
            template = jinja_env.from_string(rec.manifest.get("prompt", "{{prompt}}"))
            rendered = template.render(params)

            # prepare payload
            payload = {"prompt": rendered, **params}

            # Trigger pre-execution hooks with payload
            pre_execution_context = {
                "intent": intent,
                "payload": payload,
                "rendered_prompt": rendered,
                "sandbox_enabled": rec.manifest.get("sandbox", True),
                "plugin_manifest": rec.manifest,
                "dispatch_id": dispatch_context["dispatch_id"]
            }
            
            await self.trigger_hook_safe(
                "plugin_pre_execution",
                pre_execution_context,
                {"roles": roles} if roles else None
            )

            # execute in sandbox or direct
            if rec.manifest.get("sandbox", True):
                # run_in_sandbox returns awaitable result
                result = await run_in_sandbox(rec.handler, payload)
            else:
                result = rec.handler(payload)
                if inspect.iscoroutine(result):
                    result = await result

            # Trigger post-execution hooks with results
            post_execution_context = {
                "intent": intent,
                "payload": payload,
                "result": result,
                "success": True,
                "plugin_manifest": rec.manifest,
                "dispatch_id": dispatch_context["dispatch_id"],
                "execution_mode": "sandbox" if rec.manifest.get("sandbox", True) else "direct"
            }
            
            await self.trigger_hook_safe(
                "plugin_post_execution",
                post_execution_context,
                {"roles": roles} if roles else None
            )

            return result

        except Exception as ex:
            # Trigger error hooks
            error_context = {
                "intent": intent,
                "params": params,
                "error": str(ex),
                "error_type": type(ex).__name__,
                "plugin_manifest": rec.manifest,
                "dispatch_id": dispatch_context["dispatch_id"],
                "recovery_actions": self._get_dispatch_recovery_actions(ex, intent)
            }
            
            await self.trigger_hook_safe(
                "plugin_dispatch_error",
                error_context,
                {"roles": roles} if roles else None
            )
            raise
    
    def _get_dispatch_recovery_actions(self, error: Exception, intent: str) -> list[str]:
        """Generate recovery actions for dispatch errors."""
        actions = []
        
        if isinstance(error, AccessDenied):
            actions.append("Check user roles and permissions")
            actions.append("Request elevated access if needed")
        elif isinstance(error, FileNotFoundError):
            actions.append("Verify plugin files exist")
            actions.append("Check plugin directory structure")
        elif "sandbox" in str(error).lower():
            actions.append("Check sandbox configuration")
            actions.append("Verify resource limits")
        else:
            actions.append(f"Check plugin '{intent}' configuration")
            actions.append("Review plugin logs for details")
        
        return actions


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
