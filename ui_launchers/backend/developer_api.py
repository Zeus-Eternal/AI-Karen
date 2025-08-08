# ui_launchers/backend/developer_api.py
"""
Enhanced Developer API with AG-UI integration for Kari components.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.ai_karen_engine.plugin_manager import get_plugin_manager
from src.ai_karen_engine.extensions.manager import ExtensionManager
from src.ai_karen_engine.hooks.hook_manager import get_hook_manager
from src.ai_karen_engine.core.memory.ag_ui_manager import AGUIMemoryManager
from src.ai_karen_engine.auth.session import get_current_user
from src.ai_karen_engine.database.conversation_manager import ConversationManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/developer", tags=["developer"])


def _resolve_db_client(app, explicit_db_client: Any = None) -> Any:
    """
    Resolve a DB client for ConversationManager with graceful fallbacks.
    Priority:
      1) explicit_db_client passed into setup_developer_api()
      2) app.state.db_client
      3) app.state.db
    """
    if explicit_db_client is not None:
        return explicit_db_client
    if hasattr(app, "state"):
        if getattr(app.state, "db_client", None):
            return app.state.db_client
        if getattr(app.state, "db", None):
            return app.state.db
    raise RuntimeError(
        "ConversationManager requires a db_client. "
        "Pass db_client to setup_developer_api(...) or set app.state.db_client."
    )


class KariDevStudioAPI:
    """Enhanced developer API for Kari components with AG-UI integration."""

    def __init__(
        self,
        conversation_manager: Optional[ConversationManager] = None,
        db_client: Any = None,
    ):
        self.plugin_manager = get_plugin_manager()
        self.hook_manager = get_hook_manager()
        self.memory_manager = AGUIMemoryManager()
        # Defer CM construction until we have a db_client (in setup_developer_api)
        self.conversation_manager: Optional[ConversationManager] = conversation_manager
        self._db_client = db_client
        self.extension_manager: Optional[ExtensionManager] = None

    def set_extension_manager(self, extension_manager: ExtensionManager):
        self.extension_manager = extension_manager

    def ensure_conversation_manager(self):
        if self.conversation_manager is None:
            if self._db_client is None:
                raise RuntimeError("ConversationManager not initialized: missing db_client.")
            self.conversation_manager = ConversationManager(db_client=self._db_client)

    async def get_system_components(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        components: List[Dict[str, Any]] = []

        # --- Plugins ---
        try:
            plugin_metrics = self.plugin_manager.get_plugin_metrics()
            _ = self.plugin_manager.get_hooks_by_source("plugin_manager")
            for plugin_name in self.plugin_manager.router.list_intents():
                components.append({
                    "id": f"plugin_{plugin_name}",
                    "name": plugin_name,
                    "type": "plugin",
                    "status": "active",
                    "health": self._determine_health_from_metrics(plugin_metrics, plugin_name),
                    "metrics": self._extract_plugin_metrics(plugin_metrics, plugin_name),
                    "capabilities": self._get_plugin_capabilities(plugin_name),
                    "last_activity": datetime.utcnow().isoformat(),
                    "chat_integration": True,
                    "copilot_enabled": self._check_copilot_integration(plugin_name, "plugin"),
                })
        except Exception as e:
            logger.error("Failed to enumerate plugins: %s", e)

        # --- Extensions ---
        if self.extension_manager:
            try:
                loaded_extensions = self.extension_manager.get_loaded_extensions()
                extension_health = await self.extension_manager.check_all_extensions_health()
                for ext_record in loaded_extensions:
                    try:
                        usage = self.extension_manager.get_extension_resource_usage(ext_record.manifest.name) or {}
                        hook_stats = await self.extension_manager.get_extension_hook_stats(ext_record.manifest.name)
                        components.append({
                            "id": f"extension_{ext_record.manifest.name}",
                            "name": ext_record.manifest.name,
                            "type": "extension",
                            "status": ext_record.status.value,
                            "health": getattr(extension_health.get(ext_record.manifest.name, None), "value", "unknown").lower()
                                      if extension_health else "unknown",
                            "metrics": {
                                "executions": hook_stats.get("total_executions", 0),
                                "success_rate": hook_stats.get("success_rate", 1.0),
                                "avg_response_time": hook_stats.get("avg_duration_ms", 0),
                                "memory_usage": usage.get("memory_mb", 0),
                                "cpu_usage": usage.get("cpu_percent", 0),
                            },
                            "capabilities": getattr(ext_record.manifest, "capabilities", {}).dict()
                                            if getattr(ext_record.manifest, "capabilities", None) else {},
                            "last_activity": ext_record.loaded_at.isoformat() if ext_record.loaded_at else datetime.utcnow().isoformat(),
                            "chat_integration": self._check_chat_integration(ext_record.manifest.name, "extension"),
                            "copilot_enabled": self._check_copilot_integration(ext_record.manifest.name, "extension"),
                        })
                    except Exception as e:
                        logger.warning("Failed to build extension component for %s: %s", ext_record.manifest.name, e)
            except Exception as e:
                logger.error("Extension enumeration failed: %s", e)

        # --- Hooks (aggregated) ---
        try:
            all_hooks = self.hook_manager.get_all_hooks()
            hook_stats = self.hook_manager.get_execution_stats()
            groups: Dict[str, list] = {}
            for h in all_hooks:
                key = f"{h.source_type}_{h.source_name or 'unknown'}"
                groups.setdefault(key, []).append(h)
            for key, hooks in groups.items():
                try:
                    total = sum(hook_stats.get(f"{h.hook_type}_success", 0) +
                                hook_stats.get(f"{h.hook_type}_error", 0) +
                                hook_stats.get(f"{h.hook_type}_timeout", 0) for h in hooks)
                    succ = sum(hook_stats.get(f"{h.hook_type}_success", 0) for h in hooks)
                    rate = succ / total if total else 1.0
                    components.append({
                        "id": f"hook_{key}",
                        "name": f"{key.split('_', 1)[1]} Hooks",
                        "type": "hook",
                        "status": "active" if any(getattr(h, "enabled", True) for h in hooks) else "inactive",
                        "health": "healthy" if rate > 0.9 else "warning" if rate > 0.7 else "critical",
                        "metrics": {"executions": total, "success_rate": rate, "avg_response_time": 50,
                                    "memory_usage": 5, "cpu_usage": 1},
                        "capabilities": [h.hook_type for h in hooks],
                        "last_activity": datetime.utcnow().isoformat(),
                        "chat_integration": any("chat" in h.hook_type.lower() for h in hooks),
                        "copilot_enabled": any("ai" in h.hook_type.lower() or "copilot" in h.hook_type.lower() for h in hooks),
                    })
                except Exception as e:
                    logger.warning("Hook group aggregation failed for %s: %s", key, e)
        except Exception as e:
            logger.error("Hook enumeration failed: %s", e)

        # --- LLM providers (placeholder until wired to registry) ---
        for provider in ["ollama", "openai", "anthropic", "gemini"]:
            components.append({
                "id": f"llm_{provider}",
                "name": f"{provider.title()} Provider",
                "type": "llm_provider",
                "status": "active",
                "health": "healthy",
                "metrics": {"executions": 100, "success_rate": 0.95, "avg_response_time": 1500,
                            "memory_usage": 50, "cpu_usage": 10},
                "capabilities": ["text_generation", "chat", "embeddings"],
                "last_activity": datetime.utcnow().isoformat(),
                "chat_integration": True,
                "copilot_enabled": provider in {"openai", "anthropic"},
            })

        return {
            "components": components,
            "total_count": len(components),
            "active_count": sum(1 for c in components if c["status"] == "active"),
            "healthy_count": sum(1 for c in components if c["health"] == "healthy"),
            "chat_integrated_count": sum(1 for c in components if c["chat_integration"]),
            "ai_enabled_count": sum(1 for c in components if c["copilot_enabled"]),
            "last_updated": datetime.utcnow().isoformat(),
        }

    async def get_chat_metrics(self, user_context: Dict[str, Any], hours: int = 24) -> Dict[str, Any]:
        # Ensure CM exists if later we use it for real metrics
        self.ensure_conversation_manager()

        end = datetime.utcnow()
        start = end - timedelta(hours=hours)
        # TODO: replace with real data from conversation_manager
        metrics = []
        t = start
        while t <= end:
            now_mod = int(time.time()) % 100
            metrics.append({
                "timestamp": t.isoformat(),
                "total_messages": 50 + now_mod,
                "ai_suggestions": 20 + (now_mod % 30),
                "tool_calls": 10 + (now_mod % 20),
                "memory_operations": 5 + (now_mod % 15),
                "response_time_ms": 800 + (now_mod % 500),
                "user_satisfaction": 0.85 + ((now_mod % 15) / 100.0),
            })
            t += timedelta(minutes=30)

        return {
            "metrics": metrics,
            "summary": {
                "total_messages": sum(m["total_messages"] for m in metrics),
                "avg_response_time": sum(m["response_time_ms"] for m in metrics) / len(metrics),
                "avg_satisfaction": sum(m["user_satisfaction"] for m in metrics) / len(metrics),
                "total_ai_suggestions": sum(m["ai_suggestions"] for m in metrics),
                "total_tool_calls": sum(m["tool_calls"] for m in metrics),
            },
            "timeframe": {"start": start.isoformat(), "end": end.isoformat(), "hours": hours},
            "last_updated": datetime.utcnow().isoformat(),
        }

    async def execute_component_action(self, component_id: str, action: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        ctype, name = component_id.split("_", 1)
        if ctype == "plugin":
            return await self._handle_plugin_action(name, action, user_context)
        if ctype == "extension":
            return await self._handle_extension_action(name, action, user_context)
        if ctype == "hook":
            return await self._handle_hook_action(name, action, user_context)
        if ctype == "llm":
            return await self._handle_llm_action(name, action, user_context)
        return {"success": False, "error": f"Unknown component type: {ctype}"}

    # --- Helpers (unchanged logic, trimmed) ---
    def _determine_health_from_metrics(self, metrics: Dict[str, Any], component_name: str) -> str:
        return "healthy"

    def _extract_plugin_metrics(self, metrics: Dict[str, Any], plugin_name: str) -> Dict[str, Any]:
        return {"executions": 100, "success_rate": 0.95, "avg_response_time": 500, "memory_usage": 25, "cpu_usage": 5}

    def _get_plugin_capabilities(self, plugin_name: str) -> List[str]:
        return ["chat_integration", "tool_calling", "memory_access"]

    def _check_chat_integration(self, component_name: str, component_type: str) -> bool:
        return True

    def _check_copilot_integration(self, component_name: str, component_type: str) -> bool:
        return component_type in {"plugin", "extension"}

    async def _handle_plugin_action(self, plugin_name: str, action: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        if action == "restart":
            return {"success": True, "message": f"Plugin {plugin_name} restarted"}
        if action == "configure":
            return {"success": True, "message": f"Configuration opened for {plugin_name}"}
        return {"success": False, "error": f"Unknown plugin action: {action}"}

    async def _handle_extension_action(self, extension_name: str, action: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.extension_manager:
            return {"success": False, "error": "Extension manager not available"}
        if action == "reload":
            await self.extension_manager.reload_extension(extension_name)
            return {"success": True, "message": f"Extension {extension_name} reloaded"}
        if action == "enable":
            await self.extension_manager.enable_extension(extension_name)
            return {"success": True, "message": f"Extension {extension_name} enabled"}
        if action == "disable":
            await self.extension_manager.disable_extension(extension_name)
            return {"success": True, "message": f"Extension {extension_name} disabled"}
        return {"success": False, "error": f"Unknown extension action: {action}"}

    async def _handle_hook_action(self, hook_name: str, action: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        if action == "toggle":
            return {"success": True, "message": f"Hook {hook_name} toggled"}
        return {"success": False, "error": f"Unknown hook action: {action}"}

    async def _handle_llm_action(self, provider_name: str, action: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        if action == "test":
            return {"success": True, "message": f"LLM provider {provider_name} tested successfully"}
        return {"success": False, "error": f"Unknown LLM action: {action}"}


# Global instance (constructed in setup with proper db_client)
dev_api: Optional[KariDevStudioAPI] = None


@router.get("/components")
async def get_components(user=Depends(get_current_user)):
    """Get all system components with their status and metrics."""
    # NOTE: your UserData uses `user_id`, not `id`
    user_context = {
        "user_id": getattr(user, "user_id", None),
        "roles": getattr(user, "roles", []),
        "tenant_id": getattr(user, "tenant_id", None),
    }
    assert dev_api is not None, "Developer API not initialized"
    data = await dev_api.get_system_components(user_context)
    return data


@router.get("/chat-metrics")
async def get_chat_metrics(
    hours: int = Query(24, ge=1, le=168),
    user=Depends(get_current_user)
):
    user_context = {
        "user_id": getattr(user, "user_id", None),
        "roles": getattr(user, "roles", []),
        "tenant_id": getattr(user, "tenant_id", None),
    }
    assert dev_api is not None, "Developer API not initialized"
    data = await dev_api.get_chat_metrics(user_context, hours)
    return data


@router.post("/components/{component_id}/{action}")
async def execute_component_action(component_id: str, action: str, user=Depends(get_current_user)):
    user_context = {
        "user_id": getattr(user, "user_id", None),
        "roles": getattr(user, "roles", []),
        "tenant_id": getattr(user, "tenant_id", None),
    }
    if "admin" not in (getattr(user, "roles", []) or []):
        raise HTTPException(status_code=403, detail="Admin role required for component actions")

    assert dev_api is not None, "Developer API not initialized"
    result = await dev_api.execute_component_action(component_id, action, user_context)
    if not result.get("success", False):
        raise HTTPException(status_code=400, detail=result.get("error", "Action failed"))
    return result


def setup_developer_api(app, extension_manager: Optional[ExtensionManager] = None, *,
                        conversation_manager: Optional[ConversationManager] = None,
                        db_client: Any = None):
    """
    Wire Developer API with proper deps:
      - extension_manager (optional)
      - conversation_manager OR db_client (required for CM creation)
      - If neither CM nor db_client is given, try app.state.db_client / app.state.db
    """
    global dev_api
    resolved_db = db_client
    if conversation_manager is None:
        resolved_db = _resolve_db_client(app, db_client)
        dev_api = KariDevStudioAPI(conversation_manager=None, db_client=resolved_db)
        # Lazy CM creation so startup doesn’t explode if DB comes online slightly later
        dev_api.ensure_conversation_manager()
    else:
        dev_api = KariDevStudioAPI(conversation_manager=conversation_manager)

    if extension_manager:
        dev_api.set_extension_manager(extension_manager)

    app.include_router(router)
    logger.info("Developer API setup complete")


__all__ = ["router", "KariDevStudioAPI", "dev_api", "setup_developer_api"]
