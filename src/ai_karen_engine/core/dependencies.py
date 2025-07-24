"""
Dependency Injection for AI Karen Engine Integration.

This module provides dependency injection helpers for FastAPI routes
and other components that need access to the integrated services.
"""

import logging
from typing import Optional
from fastapi import Depends, HTTPException

from ai_karen_engine.core.service_registry import (
    get_service_registry,
    AIOrchestrator,
    WebUIMemoryService,
    WebUIConversationService,
    PluginService,
    ToolService,
    AnalyticsService
)
from ai_karen_engine.core.config_manager import get_config, AIKarenConfig
from ai_karen_engine.core.health_monitor import get_health_monitor, HealthMonitor

logger = logging.getLogger(__name__)


# Configuration dependency
async def get_current_config() -> AIKarenConfig:
    """Get current configuration."""
    try:
        return get_config()
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        raise HTTPException(status_code=500, detail="Configuration unavailable")


# Service dependencies
async def get_ai_orchestrator_service() -> AIOrchestrator:
    """Get AI Orchestrator service instance."""
    try:
        registry = get_service_registry()
        return await registry.get_service("ai_orchestrator")
    except Exception as e:
        logger.error(f"Failed to get AI Orchestrator service: {e}")
        raise HTTPException(status_code=503, detail="AI Orchestrator service unavailable")


async def get_memory_service() -> WebUIMemoryService:
    """Get Memory service instance."""
    try:
        registry = get_service_registry()
        return await registry.get_service("memory_service")
    except Exception as e:
        logger.error(f"Failed to get Memory service: {e}")
        raise HTTPException(status_code=503, detail="Memory service unavailable")


async def get_conversation_service() -> WebUIConversationService:
    """Get Conversation service instance."""
    try:
        registry = get_service_registry()
        return await registry.get_service("conversation_service")
    except Exception as e:
        logger.error(f"Failed to get Conversation service: {e}")
        raise HTTPException(status_code=503, detail="Conversation service unavailable")


async def get_plugin_service() -> PluginService:
    """Get Plugin service instance."""
    try:
        registry = get_service_registry()
        return await registry.get_service("plugin_service")
    except Exception as e:
        logger.error(f"Failed to get Plugin service: {e}")
        raise HTTPException(status_code=503, detail="Plugin service unavailable")


async def get_tool_service() -> ToolService:
    """Get Tool service instance."""
    try:
        registry = get_service_registry()
        return await registry.get_service("tool_service")
    except Exception as e:
        logger.error(f"Failed to get Tool service: {e}")
        raise HTTPException(status_code=503, detail="Tool service unavailable")


async def get_analytics_service() -> AnalyticsService:
    """Get Analytics service instance."""
    try:
        registry = get_service_registry()
        return await registry.get_service("analytics_service")
    except Exception as e:
        logger.error(f"Failed to get Analytics service: {e}")
        raise HTTPException(status_code=503, detail="Analytics service unavailable")


# Health monitoring dependency
async def get_health_monitor_service() -> HealthMonitor:
    """Get Health Monitor service instance."""
    try:
        return get_health_monitor()
    except Exception as e:
        logger.error(f"Failed to get Health Monitor: {e}")
        raise HTTPException(status_code=503, detail="Health Monitor unavailable")


# Service registry dependency
async def get_service_registry_instance():
    """Get Service Registry instance."""
    try:
        return get_service_registry()
    except Exception as e:
        logger.error(f"Failed to get Service Registry: {e}")
        raise HTTPException(status_code=503, detail="Service Registry unavailable")


# Convenience dependencies for common combinations
async def get_ai_services() -> tuple[AIOrchestrator, WebUIMemoryService, WebUIConversationService]:
    """Get core AI services (orchestrator, memory, conversation)."""
    try:
        registry = get_service_registry()
        orchestrator = await registry.get_service("ai_orchestrator")
        memory = await registry.get_service("memory_service")
        conversation = await registry.get_service("conversation_service")
        return orchestrator, memory, conversation
    except Exception as e:
        logger.error(f"Failed to get AI services: {e}")
        raise HTTPException(status_code=503, detail="AI services unavailable")


async def get_execution_services() -> tuple[PluginService, ToolService]:
    """Get execution services (plugin, tool)."""
    try:
        registry = get_service_registry()
        plugin = await registry.get_service("plugin_service")
        tool = await registry.get_service("tool_service")
        return plugin, tool
    except Exception as e:
        logger.error(f"Failed to get execution services: {e}")
        raise HTTPException(status_code=503, detail="Execution services unavailable")


# FastAPI dependency aliases for easier use in routes
AIOrchestrator_Dep = Depends(get_ai_orchestrator_service)
MemoryService_Dep = Depends(get_memory_service)
ConversationService_Dep = Depends(get_conversation_service)
PluginService_Dep = Depends(get_plugin_service)
ToolService_Dep = Depends(get_tool_service)
AnalyticsService_Dep = Depends(get_analytics_service)
Config_Dep = Depends(get_current_config)
HealthMonitor_Dep = Depends(get_health_monitor_service)
ServiceRegistry_Dep = Depends(get_service_registry_instance)
