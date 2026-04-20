"""
Dependency Injection Framework for AI Karen Engine.

This module provides a unified, production-grade dependency management system.
It supports multiple resolution strategies:
1. Dynamic Service Registry (Primary)
2. Optimized Lazy Loading (Secondary Fallback)
3. Direct Factory Injection (Final Resilience Fallback)
"""

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Callable, Union, Literal, TYPE_CHECKING, cast

from fastapi import Depends, HTTPException, Request

from ai_karen_engine.config.config_manager import AIKarenConfig, get_config
from ai_karen_engine.core.health_monitor import HealthMonitor, get_health_monitor
from ai_karen_engine.core.service_registry import get_service_registry
from ai_karen_engine.auth.auth_middleware import AuthenticationError

logger = logging.getLogger(__name__)

# --- Authentication Dependencies ---


def bypass_user_context_func() -> Dict[str, Any]:
    """
    Unified user context provider.
    Currently optimized for development and bypassed production scenarios.
    """
    try:
        from ai_karen_engine.core.auth_config import auth_config

        if auth_config.should_bypass_auth():
            logger.info("🔓 Auth Bypass Active: Providing elevated developer context")
            return {
                "user_id": "dev-user",
                "email": "dev-user@localhost",
                "user_type": "developer",
                "permissions": ["*"],
                "tenant_id": "dev-tenant",
                "roles": ["admin", "user"],
                "is_active": True,
                "token_id": str(uuid.uuid4()),
                "authenticated": True,
            }

        # In a "fresh app" state, we prioritize explicitly handled context.
        # Fallback to a safe minimum if bypass is disabled but no context exists.
        return {
            "user_id": "anonymous",
            "email": None,
            "roles": [],
            "tenant_id": "default",
            "is_active": True,
        }
    except Exception as e:
        logger.error(f"Context resolution failure: {e}")
        raise HTTPException(
            status_code=401, detail="Authentication context unavailable"
        )


async def get_current_user_id(
    user_ctx: Dict[str, Any] = Depends(bypass_user_context_func),
) -> str:
    return str(user_ctx.get("user_id", "anonymous"))


async def get_current_tenant_id(
    user_ctx: Dict[str, Any] = Depends(bypass_user_context_func),
) -> str:
    return str(user_ctx.get("tenant_id", "dev-tenant"))


# --- Core Service Resolution Helper ---


async def _resolve_service(
    service_name: str, factory_func: Optional[Callable] = None
) -> Any:
    """
    internal helper following the DRY principle for service discovery.
    Tries Registry -> Lazy Loading -> Factory.
    """
    # 1. Primary: Service Registry
    try:
        registry = get_service_registry()
        service = await registry.get_service(service_name)
        if service:
            return service
    except Exception as e:
        logger.debug(f"Registry lookup for {service_name} missed: {e}")

    # 2. Secondary: Lazy Loading
    try:
        from ai_karen_engine.core.lazy_loading import lazy_registry, setup_lazy_services

        if not lazy_registry.list_services():
            await setup_lazy_services()

        service = await lazy_registry.get_service_instance(service_name)
        if service:
            return service
    except Exception as e:
        logger.debug(f"Lazy loading fallback for {service_name} missed: {e}")

    # 3. Final: Factory Fallback
    if factory_func:
        try:
            logger.info(
                f"🔄 Final resilience fallback: Executing factory for {service_name}"
            )
            service = await factory_func()
            if service:
                return service
        except Exception as e:
            logger.error(f"❌ Factory fallback for {service_name} failed: {e}")

    logger.error(f"❌ Critical Service Failure: {service_name} is unavailable.")
    raise HTTPException(
        status_code=503, detail=f"Service '{service_name}' is currently unavailable."
    )


# --- Public Service Dependencies ---


async def get_ai_orchestrator_service() -> Any:
    """Discovery for AI Orchestrator."""
    return await _resolve_service("ai_orchestrator")


async def get_memory_service() -> Any:
    """Discovery for Memory service."""
    return await _resolve_service("memory_service")


async def get_conversation_service() -> Any:
    """Discovery for Conversation service with complex legacy mapping support."""

    async def factory():
        from ai_karen_engine.chat.factory import get_chat_service_factory
        from ai_karen_engine.memory.conversation_service import ConversationService
        from ai_karen_engine.memory.memory_service import WebUIMemoryService

        factory_inst = get_chat_service_factory()
        base_manager = factory_inst.create_conversation_manager()
        memory_service = factory_inst.create_memory_service() or WebUIMemoryService()

        if not base_manager:
            return None

        # Inline minimal adapter if needed, though ideally this should be in a factory
        return ConversationService(
            base_conversation_manager=cast(Any, base_manager),
            memory_service=memory_service,
        )

    return await _resolve_service("conversation_service", factory)


async def get_plugin_service() -> Any:
    async def factory():
        from pathlib import Path
        from ai_karen_engine.infra.plugin_service import (
            get_plugin_service as get_infra_plugin_service,
            initialize_plugin_service,
        )

        expected_path = Path("src/ai_karen_engine/extensions/plugins")
        service = get_infra_plugin_service()

        if (
            not getattr(service, "initialized", False)
            or getattr(service, "marketplace_path", None) != expected_path
            or getattr(service, "core_plugins_path", None) != expected_path
        ):
            service = await initialize_plugin_service(
                marketplace_path=expected_path,
                core_plugins_path=expected_path,
                auto_discover=True,
            )
        else:
            # Service initialized but maybe not discovered lately
            await service.discover_plugins()
            await service.validate_and_register_all_discovered()

        # Automatically trigger UI materialization to sync files to plugin_repo
        try:
            from ai_karen_engine.extensions.platform.core.registry.ui_materialization import (
                get_ui_pipeline,
            )

            pipeline = get_ui_pipeline()
            # This is an async call but we can run it in the background or await it
            await pipeline.materialize_all()
            logger.info(
                "UI materialization completed during plugin service acquisition"
            )
        except Exception as ui_err:
            logger.warning(f"Auto UI materialization failed: {ui_err}")

        return service

    return await _resolve_service("plugin_service", factory)


async def get_tool_service() -> Any:
    async def factory():
        from ai_karen_engine.services.tool_service import ToolService

        return ToolService()

    return await _resolve_service("tool_service", factory)


async def get_analytics_service() -> Any:
    return await _resolve_service("analytics_service")


async def get_current_config() -> AIKarenConfig:
    return get_config()


async def get_health_monitor_service() -> HealthMonitor:
    return get_health_monitor()


async def get_service_registry_instance() -> Any:
    return get_service_registry()


# --- Dependency Injection Aliases (The API Surface) ---

Config_Dep = Depends(get_current_config)
HealthMonitor_Dep = Depends(get_health_monitor_service)
ServiceRegistry_Dep = Depends(get_service_registry_instance)

AIOrchestrator_Dep = Depends(get_ai_orchestrator_service)
MemoryService_Dep = Depends(get_memory_service)
ConversationService_Dep = Depends(get_conversation_service)

PluginService_Dep = Depends(get_plugin_service)
ToolService_Dep = Depends(get_tool_service)
AnalyticsService_Dep = Depends(get_analytics_service)

UserContext_Dep = Depends(bypass_user_context_func)
UserId_Dep = Depends(get_current_user_id)
TenantId_Dep = Depends(get_current_tenant_id)
