import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI

from ai_karen_engine.server.plugin_loader import load_plugins
from ai_karen_engine.server.optimized_startup import (
    initialize_optimization_components,
    optimized_service_startup,
    initialize_performance_monitoring,
    integrate_with_existing_logging,
    run_startup_audit,
    cleanup_optimization_components,
    load_plugins_optimized
)

logger = logging.getLogger(__name__)

_registry_refresh_task: Optional[asyncio.Task] = None
_startup_init_task: Optional[asyncio.Task] = None
_optimization_enabled: bool = True


async def init_database() -> None:
    """Initialize database connections - deferred to when actually needed."""
    # Database initialization is now handled by server/database_config.py
    # and only happens when database is available
    logger.debug("Database initialization deferred (lazy loading)")


async def init_ai_services(settings: Any) -> None:
    """Initialize all AI-related services with optimization"""
    global _optimization_enabled
    
    # Check if optimization is enabled
    _optimization_enabled = getattr(settings, 'enable_performance_optimization', 
                                  os.getenv('ENABLE_PERFORMANCE_OPTIMIZATION', 'true').lower() == 'true')
    
    # Check for lazy loading mode
    lazy_loading_enabled = os.getenv('KARI_LAZY_LOADING', 'true').lower() == 'true'
    
    try:
        if lazy_loading_enabled:
            logger.info("⚡ Using ultra-optimized lazy loading startup")
            
            # Use the new optimized startup system
            from ai_karen_engine.core.optimized_startup import optimized_startup_sequence
            startup_report = await optimized_startup_sequence(settings)
            
            logger.info("✅ Lazy loading startup completed")
            logger.info(f"   • Startup time: {startup_report.get('startup_time', 0):.2f}s")
            logger.info(f"   • Mode: {startup_report.get('mode', 'optimized')}")
            logger.info(f"   • Initialized services: {len(startup_report.get('initialized_services', []))}")
            
        elif _optimization_enabled:
            logger.info("🚀 Using optimized service initialization")
            
            # Initialize optimization components first
            optimization_report = await initialize_optimization_components(settings)
            
            # Run startup audit for baseline
            audit_report = await run_startup_audit(settings)
            
            # Use optimized service startup
            startup_report = await optimized_service_startup(settings)
            
            # Initialize performance monitoring
            await initialize_performance_monitoring(settings)
            
            # Integrate with existing logging
            await integrate_with_existing_logging(settings)
            
            # Load plugins with optimization
            await load_plugins_optimized(settings.plugin_dir, settings)
            
            logger.info("✅ Optimized AI services initialization completed")
            logger.info(f"   • Optimization time: {optimization_report.get('initialization_time', 0):.2f}s")
            logger.info(f"   • Startup time: {startup_report.get('startup_time', 0):.2f}s")
            
        else:
            logger.info("📦 Using standard service initialization")
            
            # Standard initialization path
            from ai_karen_engine.core.memory import manager as memory_manager
            memory_manager.init_memory()
            load_plugins(settings.plugin_dir)

            # Initialize model orchestrator plugin if enabled
            try:
                from ai_karen_engine.server.plugin_loader import ENABLED_PLUGINS
                if "model_orchestrator" in ENABLED_PLUGINS:
                    from plugin_marketplace.ai.model_orchestrator.service import ModelOrchestratorService
                    orchestrator_service = ModelOrchestratorService()
                    await orchestrator_service.initialize()
                    logger.info("Model orchestrator plugin initialized")
            except Exception as e:
                logger.warning("Model orchestrator plugin initialization failed: %s", str(e))

            from ai_karen_engine.integrations.model_discovery import sync_registry
            sync_registry()
            
            # Initialize the service registry and all services
            from ai_karen_engine.core.service_registry import initialize_services
            await initialize_services()
            
            logger.info("AI services initialized")
            
    except Exception as e:  # pragma: no cover - defensive
        logger.error("AI services initialization failed: %s", str(e))
        if lazy_loading_enabled or _optimization_enabled:
            logger.info("🔄 Falling back to minimal startup")
            
            # Fallback to ultra-minimal mode
            try:
                logger.info("⚡ Using minimal fallback initialization")
                
                from ai_karen_engine.core.optimized_startup import MinimalStartupMode
                startup_report = await MinimalStartupMode.initialize(settings)
                
                logger.info("✅ Minimal fallback initialization completed")
                logger.info(f"   • Startup time: {startup_report.get('startup_time', 0):.2f}s")
                
            except Exception as fallback_error:
                logger.error("Minimal fallback also failed: %s", str(fallback_error))
                # Last resort: basic initialization
                logger.info("🔄 Last resort: basic initialization")
                from ai_karen_engine.core.memory import manager as memory_manager
                memory_manager.init_memory()
                logger.info("Basic initialization completed")
        else:
            raise


async def cleanup_ai_services() -> None:
    """Cleanup AI resources with optimization"""
    try:
        if _optimization_enabled:
            logger.info("🧹 Using optimized cleanup")
            # Cleanup optimization components first
            await cleanup_optimization_components()
        
        # Check if lazy services are enabled
        lazy_loading_enabled = os.getenv('KARI_LAZY_LOADING', 'true').lower() == 'true'
        
        if lazy_loading_enabled:
            logger.info("🧹 Cleaning up lazy services")
            from ai_karen_engine.core.lazy_loading import cleanup_lazy_services
            await cleanup_lazy_services()
        
        # Standard cleanup
        try:
            from ai_karen_engine.core.service_registry import get_service_registry
            registry = get_service_registry()
            await registry.shutdown()
        except Exception as e:
            logger.warning(f"Service registry cleanup failed: {e}")
        
        logger.info("✅ AI services cleanup completed")
        
    except Exception as e:
        logger.error(f"Error during AI services cleanup: {e}")
        
        from ai_karen_engine.core.memory import manager as memory_manager
        await memory_manager.close()
        
        logger.info("AI services cleanup completed")
    except Exception as e:  # pragma: no cover - defensive
        logger.error("AI services cleanup failed: %s", str(e))


def init_security(settings: Any) -> None:
    """Initialize security components"""
    if settings.secret_key == "changeme" and settings.environment == "production":
        logger.critical("Insecure default secret key in production!")
    logger.info("Security components initialized")


def start_background_tasks(settings: Any) -> None:
    """Start background tasks"""
    global _registry_refresh_task

    if settings.llm_refresh_interval > 0:
        async def _periodic_refresh() -> None:
            from ai_karen_engine.integrations.model_discovery import sync_registry

            while True:  # pragma: no branch
                await asyncio.sleep(settings.llm_refresh_interval)
                sync_registry()

        _registry_refresh_task = asyncio.create_task(_periodic_refresh())
        logger.info("Started model registry refresh task")


async def stop_background_tasks() -> None:
    """Stop background tasks"""
    global _registry_refresh_task

    if _registry_refresh_task:
        _registry_refresh_task.cancel()
        try:
            await _registry_refresh_task
        except asyncio.CancelledError:  # pragma: no cover - expected
            logger.info("Background tasks stopped")
        except Exception as e:  # pragma: no cover - defensive
            logger.error("Error stopping background tasks: %s", str(e))


async def on_startup(settings: Any) -> None:
    global _startup_init_task
    logger.info("Starting Kari AI Server in %s mode", settings.environment)
    await init_database()
    
    # Fast-startup mode: don't block server readiness on heavy init
    fast_start = os.getenv("KARI_FAST_STARTUP", os.getenv("FAST_STARTUP", "true")).lower() in ("1", "true", "yes")
    if fast_start and (settings.environment or "").lower() in ("development", "dev", "local"):
        logger.info("⚡ Fast startup enabled: initializing AI services in background")
        _startup_init_task = asyncio.create_task(init_ai_services(settings))
    else:
        await init_ai_services(settings)

    init_security(settings)
    start_background_tasks(settings)
    logger.info("Server startup completed")


async def on_shutdown() -> None:
    global _startup_init_task
    logger.info("Shutting down Kari AI Server")
    # If background startup is still running, cancel it gracefully
    if _startup_init_task and not _startup_init_task.done():
        _startup_init_task.cancel()
        try:
            await _startup_init_task
        except asyncio.CancelledError:
            logger.info("Background startup task cancelled")
        except Exception as e:
            logger.warning("Background startup task error during shutdown: %s", e)
        finally:
            _startup_init_task = None
    await stop_background_tasks()
    await cleanup_ai_services()
    logger.info("Server shutdown completed")


def create_lifespan(settings: Any):
    """Create a lifespan context manager bound to settings"""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await on_startup(settings)
        try:
            yield
        finally:
            await on_shutdown()

    return lifespan
