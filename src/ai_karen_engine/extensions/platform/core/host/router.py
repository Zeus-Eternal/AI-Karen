import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from datetime import datetime

from ai_karen_engine.extensions.platform.core.manifest import (
    ExtensionRecord,
    ExtensionStatus,
    ExtensionManifest,
    HookPoint,
    HookContext,
)
from ..registry.plugin_registry import get_registry
from .loader import ExtensionLoader
from .runner import ExtensionRunner

logger = logging.getLogger("kari.plugin_router")


class PluginRouter:
    """
    Ruthless Prompt-First Plugin Orchestrator.
    Back-ends into ExtensionLoader for loading and ExtensionRunner for execution.
    """

    def __init__(self, extensions_dir: str = "src/extensions"):
        self.registry = get_registry()
        self.loader = ExtensionLoader(extensions_dir)
        # ExtensionRunner needs an ExtensionRegistry (legacy type).
        # For now, we'll pass our unified registry and refine the interface if needed.
        self.runner = ExtensionRunner(self.registry)

    async def reload(self):
        """Discovers and reloads all extensions."""
        await self.registry.refresh()
        discovered = self.registry.list_discovered()
        for ext_id in discovered:
            try:
                # Try to load via the official Loader
                instance = self.loader.load_extension(ext_id)
                # Register the loaded instance back to the registry for truth
                record = ExtensionRecord(
                    manifest=instance.manifest,
                    instance=instance,
                    status=ExtensionStatus.ACTIVE,
                    directory=Path(self.loader.extensions_dir) / ext_id,
                    loaded_at=datetime.now(),
                )
                self.registry.register_loaded_instance(record)
            except Exception as e:
                logger.error(f"Failed to load extension {ext_id}: {e}")

    async def dispatch(
        self, intent: str, params: Dict[str, Any], roles: Optional[List[str]] = None
    ) -> Any:
        """
        Primary entry point for AI-triggered plugins.
        Maps an 'intent' to an extension and executes it.
        """
        # 1. Find the extension providing this intent
        # (For now, we assume extension name == primary intent if not specified)
        extension_record = self.registry.get_extension(intent)
        if not extension_record:
            # Try searching by manifest metadata if not direct match
            for rec in self.registry.list_extensions():
                if getattr(rec.manifest, "intent", None) == intent:
                    extension_record = rec
                    break

        if not extension_record:
            raise RuntimeError(f"No extension found for intent '{intent}'")

        # 2. Execute via Runner (with full isolation, metrics, and hooks)
        # We wrap the parameters into a HookContext
        context = HookContext(
            hook_point=HookPoint.PRE_INTENT_DETECTION,  # Placeholder for custom dispatch hook
            data=params,
            user_context={"roles": roles} if roles else {},
        )

        try:
            # We can either use runner.execute_hook for standard points,
            # or directly call the extension instance.
            # Here we prefer the safe execution wrapper.
            result = await self.runner._execute_extension_with_timeout(
                extension_record.instance,
                HookPoint.POST_LLM_RESULT,  # Example point for execution
                context,
                timeout=30.0,
            )
            return result
        except Exception as e:
            logger.error(f"Dispatch error for intent {intent}: {e}")
            raise

    def get_api_router(self) -> Any:
        """Mounts all extensions that provide an API router."""
        from fastapi import APIRouter

        router = APIRouter()
        for record in self.registry.list_extensions():
            if record.instance and hasattr(record.instance, "get_api_router"):
                ext_router = record.instance.get_api_router()
                if ext_router:
                    router.include_router(ext_router)
        return router


# Singleton accessor
_router_instance: Optional[PluginRouter] = None


def get_plugin_router() -> PluginRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = PluginRouter()
    return _router_instance
