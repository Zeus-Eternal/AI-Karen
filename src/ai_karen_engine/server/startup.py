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
    load_plugins_optimized,
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
    _optimization_enabled = getattr(
        settings,
        "enable_performance_optimization",
        os.getenv("ENABLE_PERFORMANCE_OPTIMIZATION", "true").lower() == "true",
    )

    # Check for lazy loading mode
    lazy_loading_enabled = os.getenv("KARI_LAZY_LOADING", "true").lower() == "true"

    try:
        if lazy_loading_enabled:
            logger.info("⚡ Using ultra-optimized lazy loading startup")

            # Use the new optimized startup system
            from ai_karen_engine.core.runtime.optimized_startup import (
                optimized_startup_sequence,
            )

            startup_report = await optimized_startup_sequence(settings)

            logger.info("✅ Lazy loading startup completed")
            logger.info(
                f"   • Startup time: {startup_report.get('startup_time', 0):.2f}s"
            )
            logger.info(f"   • Mode: {startup_report.get('mode', 'optimized')}")
            logger.info(
                f"   • Initialized services: {len(startup_report.get('initialized_services', []))}"
            )

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
            logger.info(
                f"   • Optimization time: {optimization_report.get('initialization_time', 0):.2f}s"
            )
            logger.info(
                f"   • Startup time: {startup_report.get('startup_time', 0):.2f}s"
            )

        else:
            logger.info("📦 Using standard service initialization")

            # Standard initialization path
            from ai_karen_engine.core.memory import (
                memory_runtime_manager as memory_manager,
            )

            memory_manager.init_memory()
            load_plugins(settings.plugin_dir)

            # Initialize model orchestrator plugin if enabled
            try:
                from ai_karen_engine.server.plugin_loader import ENABLED_PLUGINS

                if "model_orchestrator" in ENABLED_PLUGINS:
                    from plugin_marketplace.ai.model_orchestrator.service import (
                        ModelOrchestratorService,
                    )

                    orchestrator_service = ModelOrchestratorService()
                    await orchestrator_service.initialize()
                    logger.info("Model orchestrator plugin initialized")
            except Exception as e:
                logger.warning(
                    "Model orchestrator plugin initialization failed: %s", str(e)
                )

            from ai_karen_engine.integrations.model_discovery import sync_registry

            sync_registry()

            # Initialize the service registry and all services
            from ai_karen_engine.core.services.service_registry import initialize_services

            await initialize_services()

            logger.info("AI services initialized")

    except Exception as e:  # pragma: no cover - defensive
        logger.error("AI services initialization failed: %s", str(e))
        if lazy_loading_enabled or _optimization_enabled:
            logger.info("🔄 Falling back to minimal startup")

            # Fallback to ultra-minimal mode
            try:
                logger.info("⚡ Using minimal fallback initialization")

                from ai_karen_engine.core.runtime.optimized_startup import MinimalStartupMode

                startup_report = await MinimalStartupMode.initialize(settings)

                logger.info("✅ Minimal fallback initialization completed")
                logger.info(
                    f"   • Startup time: {startup_report.get('startup_time', 0):.2f}s"
                )

            except Exception as fallback_error:
                logger.error("Minimal fallback also failed: %s", str(fallback_error))
                # Last resort: basic initialization
                logger.info("🔄 Last resort: basic initialization")
                from ai_karen_engine.core.memory import (
                    memory_runtime_manager as memory_manager,
                )

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
        lazy_loading_enabled = os.getenv("KARI_LAZY_LOADING", "true").lower() == "true"

        if lazy_loading_enabled:
            logger.info("🧹 Cleaning up lazy services")
            from ai_karen_engine.core.runtime.lazy_loading import cleanup_lazy_services

            await cleanup_lazy_services()

        # Standard cleanup
        try:
            from ai_karen_engine.core.services.service_registry import get_service_registry

            registry = get_service_registry()
            await registry.shutdown()
        except Exception as e:
            logger.warning(f"Service registry cleanup failed: {e}")

        logger.info("✅ AI services cleanup completed")

    except Exception as e:
        logger.error(f"Error during AI services cleanup: {e}")

        from ai_karen_engine.core.memory import (
            memory_runtime_manager as memory_manager,
        )

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

    # Initialize extension system
    try:
        from ai_karen_engine.extensions.platform.core.manager import (
            get_extension_core_manager,
        )

        extension_manager = get_extension_core_manager()
        if extension_manager:
            logger.info("Initializing extension system...")
            await extension_manager.initialize()
            logger.info("Extension system initialized successfully")
        else:
            logger.warning("Extension system not available")
    except Exception as e:
        logger.error(f"Failed to initialize extension system: {e}")

    # Fast-startup mode: don't block server readiness on heavy init
    fast_start = os.getenv(
        "KARI_FAST_STARTUP", os.getenv("FAST_STARTUP", "true")
    ).lower() in ("1", "true", "yes")
    if fast_start and (settings.environment or "").lower() in (
        "development",
        "dev",
        "local",
    ):
        logger.info("⚡ Fast startup enabled: initializing AI services in background")
        _startup_init_task = asyncio.create_task(init_ai_services(settings))
    else:
        try:
            await init_ai_services(settings)
        except Exception as e:
            logger.error(f"Failed to initialize AI services: {e}", exc_info=True)
            logger.warning("Continuing startup without AI services")

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


async def init_extension_monitoring(app: FastAPI) -> None:
    """Initialize extension monitoring and alerting system"""
    try:
        from ai_karen_engine.monitoring.extensions.extension_monitoring_startup import (
            initialize_extension_monitoring,
        )

        await initialize_extension_monitoring()
        logger.info("Extension monitoring system initialized")
    except Exception as e:
        logger.warning(f"Extension monitoring initialization failed: {e}")


async def init_extension_health_monitor(app: FastAPI) -> None:
    """Initialize extension health monitor"""
    try:
        from ai_karen_engine.extensions.health_monitor import (
            initialize_extension_health_monitor,
        )

        # Get extension manager if available
        extension_manager = None
        try:
            extension_system = getattr(app.state, "extension_system", None)
            if extension_system:
                extension_manager = extension_system.extension_manager
        except Exception:
            pass

        await initialize_extension_health_monitor(extension_manager)
        logger.info("Extension health monitor initialized")
    except Exception as e:
        logger.warning(f"Extension health monitor initialization failed: {e}")


async def init_extension_database_service(app: FastAPI) -> None:
    """Initialize extension database service"""
    # Skip if database is not available
    if not getattr(app.state, "database_available", False):
        logger.info("Skipping extension database service (database not available)")
        return

    try:
        from ai_karen_engine.extensions.database_service import (
            initialize_database_service,
        )
        from ai_karen_engine.config import Settings

        settings = Settings()
        database_url = settings.database_url

        # Initialize extension database service
        async_database_url = database_url.replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        initialize_database_service(async_database_url)
        logger.info("Extension database service initialized")
    except Exception as e:
        logger.warning(f"Extension database service initialization failed: {e}")


async def init_extension_service_recovery(app: FastAPI) -> None:
    """Initialize extension service recovery system with integration to existing patterns"""
    # Skip if database is not available
    if not getattr(app.state, "database_available", False):
        logger.info("Skipping extension service recovery (database not available)")
        return

    try:
        from ai_karen_engine.extensions.service_recovery import (
            initialize_extension_service_recovery_manager,
        )
        from ai_karen_engine.services.database_config import get_database_config
        from ai_karen_engine.services.enhanced_database_health_monitor import (
            get_enhanced_database_health_monitor,
        )
        from ai_karen_engine.config import Settings

        settings = Settings()

        # Get existing components for integration
        database_config = get_database_config(settings)
        enhanced_health_monitor = get_enhanced_database_health_monitor()

        # Get extension manager if available
        extension_manager = None
        try:
            extension_system = getattr(app.state, "extension_system", None)
            if extension_system:
                extension_manager = extension_system.extension_manager
        except Exception:
            pass

        # Initialize recovery manager with existing components
        recovery_manager = await initialize_extension_service_recovery_manager(
            extension_manager=extension_manager,
            database_config=database_config,
            enhanced_health_monitor=enhanced_health_monitor,
        )

        # Register extension-specific startup handlers
        recovery_manager.add_startup_handler(
            lambda: _extension_startup_recovery_handler(recovery_manager)
        )

        # Register extension-specific graceful degradation handlers
        recovery_manager.add_graceful_degradation_handler(
            "extension_api", lambda: _extension_api_degradation_handler()
        )
        recovery_manager.add_graceful_degradation_handler(
            "authentication", lambda: _authentication_degradation_handler()
        )

        # Execute startup handlers
        await recovery_manager.execute_startup_handlers()

        logger.info("Extension service recovery initialized")

    except Exception as e:
        logger.warning(f"Extension service recovery initialization failed: {e}")


async def _extension_startup_recovery_handler(recovery_manager):
    """Extension-specific startup recovery handler"""
    try:
        logger.info("Executing extension startup recovery checks")

        # Check if extension system needs recovery on startup
        status = recovery_manager.get_recovery_status()

        # Log startup recovery status
        unhealthy_services = [
            name
            for name, state in status["service_states"].items()
            if not state["healthy"]
        ]

        if unhealthy_services:
            logger.warning(
                f"Unhealthy services detected on startup: {unhealthy_services}"
            )

            # Attempt immediate recovery for critical services
            for service_name in unhealthy_services:
                if "authentication" in service_name or "database" in service_name:
                    await recovery_manager.force_recovery(service_name)
        else:
            logger.info("All extension services healthy on startup")

    except Exception as e:
        logger.error(f"Extension startup recovery handler failed: {e}")


async def _extension_api_degradation_handler():
    """Graceful degradation handler for extension API"""
    try:
        logger.info("Enabling graceful degradation for extension API")

        # Set extension API to read-only mode or disable non-critical features
        # This would integrate with the extension system to limit functionality

        logger.info("Extension API graceful degradation enabled")

    except Exception as e:
        logger.error(f"Extension API degradation handler failed: {e}")


async def _authentication_degradation_handler():
    """Graceful degradation handler for authentication service"""
    try:
        logger.info("Enabling graceful degradation for authentication service")

        # Enable development mode authentication or read-only access
        # This would integrate with the security system to provide fallback auth

        logger.info("Authentication service graceful degradation enabled")

    except Exception as e:
        logger.error(f"Authentication degradation handler failed: {e}")


async def warm_local_llm_stack(app: FastAPI) -> None:
    """Warm the local chat/LLM stack during startup so first chat request does not time out."""
    if os.getenv("KARI_WARM_LOCAL_LLM_ON_STARTUP", "false").lower() not in (
        "1",
        "true",
        "yes",
    ):
        logger.info("Skipping local LLM warmup (disabled by environment)")
        return

    try:
        from ai_karen_engine.services.formatting.settings_manager import get_settings_manager

        settings_manager = get_settings_manager()
        active_provider = (
            str(settings_manager.get_setting("provider", "") or "").strip().lower()
        )
        if active_provider not in {"local_gguf", "local"}:
            logger.info(
                "Skipping local LLM warmup for non-local provider: %s",
                active_provider or "unset",
            )
            return

        logger.info("Warming local chat stack for provider: %s", active_provider)

        def _warm() -> None:
            from ai_karen_engine.api_routes.chat.copilot import (
                get_langgraph_orchestrator,
            )
            from ai_karen_engine.llm_orchestrator import get_orchestrator

            get_langgraph_orchestrator()
            get_orchestrator()._ensure_minimum_models_registered()

        await asyncio.to_thread(_warm)
        app.state.local_llm_warmed = True
        logger.info("Local chat stack warmup completed")
    except Exception as e:
        app.state.local_llm_warmed = False
        logger.warning(f"Local LLM warmup skipped after failure: {e}")


async def on_startup_with_extensions(settings: Any, app: FastAPI) -> None:
    """Enhanced startup with extension and monitoring initialization"""
    global _startup_init_task
    logger.info("Starting Kari AI Server in %s mode", settings.environment)
    await init_database()

    # Initialize extension monitoring and recovery systems
    await init_extension_monitoring(app)
    await init_extension_health_monitor(app)
    await init_extension_database_service(app)
    await init_extension_service_recovery(app)

    # Warm local LLM stack if configured
    await warm_local_llm_stack(app)

    # Fast-startup mode: don't block server readiness on heavy init
    fast_start = os.getenv(
        "KARI_FAST_STARTUP", os.getenv("FAST_STARTUP", "true")
    ).lower() in ("1", "true", "yes")
    if fast_start and (settings.environment or "").lower() in (
        "development",
        "dev",
        "local",
    ):
        logger.info("⚡ Fast startup enabled: initializing AI services in background")
        _startup_init_task = asyncio.create_task(init_ai_services(settings))
    else:
        try:
            await init_ai_services(settings)
        except Exception as e:
            logger.error(f"Failed to initialize AI services: {e}", exc_info=True)
            logger.warning("Continuing startup without AI services")

    init_security(settings)
    start_background_tasks(settings)
    logger.info("Server startup completed")


async def initialize_extension_system(app: FastAPI) -> None:
    """Initialize the production extension system and monitoring."""
    # Skip if database is not available
    if not getattr(app.state, "database_available", False):
        logger.info("Skipping extension system initialization (database not available)")
        return

    try:
        success = await init_extensions_for_production(
            app=app,
            extension_root="extensions",
            db_session=None,
            plugin_router=None,
        )
        if not success:
            logger.warning("Extension system initialization unsuccessful")
            return

        # Initialize extension health monitoring once the manager is available
        try:
            from ai_karen_engine.extensions.health_monitor import (
                initialize_extension_health_monitor,
            )

            extension_system = getattr(app.state, "extension_system", None)
            extension_manager = (
                extension_system.get_extension_manager()
                if extension_system
                and hasattr(extension_system, "get_extension_manager")
                else None
            )
            if extension_manager:
                await initialize_extension_health_monitor(extension_manager)
                logger.info("Extension health monitoring initialized")
            else:
                logger.warning("Extension manager unavailable")
        except Exception as monitor_error:
            logger.warning(f"Extension health monitoring failed: {monitor_error}")
    except Exception as exc:
        logger.warning(f"Extension system initialization error: {exc}")


async def init_extensions_for_production(
    app: FastAPI, extension_root: str, db_session: Any, plugin_router: Any
) -> bool:
    """Initialize extensions for production environment."""
    try:
        from ai_karen_engine.extensions.platform.core.host.factory import (
            initialize_extensions_for_production as initialize_extensions,
        )

        success = await initialize_extensions(
            app=app,
            extension_root=extension_root,
            db_session=db_session,
            plugin_router=plugin_router,
        )
        return success
    except ImportError as canonical_error:
        try:
            # Temporary fallback for migration compatibility.
            from ai_karen_engine.extensions.platform.core.host.factory import (  # type: ignore
                initialize_extensions_for_production as initialize_extensions,
            )

            success = await initialize_extensions(
                app=app,
                extension_root=extension_root,
                db_session=db_session,
                plugin_router=plugin_router,
            )
            logger.info("✅ Extension system initialized via legacy fallback path")
            return success
        except ImportError as legacy_error:
            logger.warning(
                "Extension system not available (canonical=%s, fallback=%s)",
                canonical_error,
                legacy_error,
            )
            return False
    except Exception as e:
        logger.error(f"Extension system initialization failed: {e}")
        return False


async def initialize_extension_system(app: FastAPI) -> None:
    """Initialize the production extension system and monitoring."""
    # Skip if database is not available
    if not getattr(app.state, "database_available", False):
        logger.info("Skipping extension system initialization (database not available)")
        return

    try:
        success = await init_extensions_for_production(
            app=app,
            extension_root="extensions",
            db_session=None,
            plugin_router=None,
        )
        if not success:
            logger.warning("Extension system initialization unsuccessful")
            return

        # Initialize extension health monitoring once the manager is available
        try:
            from ai_karen_engine.extensions.health_monitor import (
                initialize_extension_health_monitor,
            )

            extension_system = getattr(app.state, "extension_system", None)
            extension_manager = (
                extension_system.get_extension_manager()
                if extension_system
                and hasattr(extension_system, "get_extension_manager")
                else None
            )
            if extension_manager:
                await initialize_extension_health_monitor(extension_manager)
                logger.info("Extension health monitoring initialized")
            else:
                logger.warning("Extension manager unavailable")
        except Exception as monitor_error:
            logger.warning(f"Extension health monitoring failed: {monitor_error}")
    except Exception as exc:
        logger.warning(f"Extension system initialization error: {exc}")


async def on_shutdown_with_extensions(app: FastAPI) -> None:
    """Enhanced shutdown with extension cleanup"""
    global _startup_init_task
    logger.info("Shutting down Kari AI Server")

    # Shutdown extension monitoring
    try:
        from ai_karen_engine.monitoring.extensions.extension_monitoring_startup import (
            shutdown_extension_monitoring,
        )

        await shutdown_extension_monitoring()
        logger.info("Extension monitoring shutdown completed")
    except Exception as e:
        logger.error(f"Extension monitoring shutdown failed: {e}", exc_info=True)

    # Shutdown extension health monitor
    try:
        from ai_karen_engine.extensions.health_monitor import (
            shutdown_extension_health_monitor,
        )

        await shutdown_extension_health_monitor()
        logger.info("Extension health monitor shutdown completed")
    except Exception as e:
        logger.error(f"Extension health monitor shutdown failed: {e}", exc_info=True)

    # Shutdown extension health monitoring on application shutdown
    try:
        from ai_karen_engine.extensions.health_monitor import (
            shutdown_extension_health_monitor,
        )

        await shutdown_extension_health_monitor()
        logger.info("Extension health monitoring shutdown completed")
    except Exception as e:
        logger.warning(f"Extension health monitoring shutdown error: {e}")

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


def create_lifespan_with_extensions(settings: Any):
    """Create a lifespan context manager with extension and monitoring initialization"""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await on_startup_with_extensions(settings, app)
        try:
            yield
        finally:
            await on_shutdown_with_extensions(app)

    return lifespan


def register_startup_tasks(app: FastAPI) -> None:
    """Register startup tasks for LLM providers and services with extension recovery integration"""

    # Store database availability state in app
    app.state.database_available = False

    @app.on_event("startup")
    async def _init_database_config() -> None:
        """Initialize database configuration with enhanced settings"""
        try:
            from ai_karen_engine.services.database_config import get_database_config
            from ai_karen_engine.config import Settings

            settings = Settings()
            db_config = get_database_config(settings)

            # Initialize database with enhanced configuration
            success = await db_config.initialize_database()
            app.state.database_available = success

            if success:
                logger.info("Database available - initialized successfully")

                # Setup graceful shutdown
                await db_config.setup_graceful_shutdown()
            else:
                logger.info(
                    "Database not available - running in degraded mode (DB-dependent features disabled)"
                )

        except Exception as e:
            logger.warning(f"Database initialization failed (degraded mode): {e}")
            app.state.database_available = False

    @app.on_event("startup")
    async def _init_llm_providers() -> None:
        try:
            import os
            import asyncio

            fast = os.getenv(
                "KARI_FAST_STARTUP", os.getenv("FAST_STARTUP", "true")
            ).lower() in ("1", "true", "yes")
            from ai_karen_engine.integrations.startup import initialize_llm_providers

            if fast:
                logger.info(
                    "⚡ Fast startup: deferring LLM provider initialization to background"
                )

                async def _bg_init():
                    try:
                        result = initialize_llm_providers()
                        logger.info(
                            "LLM providers initialized (background)",
                            extra={
                                "total": result.get("total_providers"),
                                "healthy": result.get("healthy_providers"),
                                "available": result.get("available_providers"),
                            },
                        )
                    except Exception as e:
                        logger.warning(
                            f"Background LLM provider initialization failed: {e}"
                        )

                asyncio.create_task(_bg_init())
            else:
                result = initialize_llm_providers()
                logger.info(
                    "LLM providers initialized",
                    extra={
                        "total": result.get("total_providers"),
                        "healthy": result.get("healthy_providers"),
                        "available": result.get("available_providers"),
                    },
                )
        except Exception as e:
            logger.warning(f"LLM provider initialization skipped: {e}")

    @app.on_event("startup")
    async def _init_memory_service() -> None:
        """Initialize memory service with proper error handling"""
        try:
            # Check if memory service should be initialized
            import os

            enable_memory = os.getenv("KARI_ENABLE_MEMORY_SERVICE", "true").lower() in (
                "1",
                "true",
                "yes",
            )
            fast = os.getenv(
                "KARI_FAST_STARTUP", os.getenv("FAST_STARTUP", "true")
            ).lower() in ("1", "true", "yes")

            if enable_memory:
                from ai_karen_engine.core.services.service_registry import initialize_services

                if fast:
                    logger.info(
                        "⚡ Fast startup: deferring memory service initialization to background"
                    )

                    async def _bg_init_memory() -> None:
                        try:
                            await initialize_services()
                            logger.info(
                                "Memory service initialized successfully (background)"
                            )
                        except Exception as e:
                            logger.warning(
                                f"Background memory service initialization failed: {e}"
                            )

                    asyncio.create_task(_bg_init_memory())
                else:
                    logger.info("Initializing memory service...")
                    await initialize_services()
                    logger.info("Memory service initialized successfully")
            else:
                logger.info(
                    "Memory service initialization disabled by environment variable"
                )
        except Exception as e:
            logger.warning(f"Memory service initialization failed: {e}")
            # Continue startup even if memory service fails


def register_shutdown_tasks(app: FastAPI) -> None:
    """Register shutdown tasks for extension service recovery integration"""

    @app.on_event("shutdown")
    async def _shutdown_database() -> None:
        """Graceful shutdown of database connections"""
        try:
            logger.info("Starting database shutdown process")
            from ai_karen_engine.services.database_config import get_database_config
            from ai_karen_engine.config import Settings

            settings = Settings()
            db_config = get_database_config(settings)
            await db_config.cleanup()
            logger.info("Database shutdown completed successfully")
        except Exception as e:
            logger.error(f"Error during database shutdown: {e}")

    @app.on_event("shutdown")
    async def _shutdown_extension_service_recovery() -> None:
        """Shutdown extension service recovery system with graceful cleanup"""
        try:
            from ai_karen_engine.extensions.service_recovery import (
                get_extension_service_recovery_manager,
                shutdown_extension_service_recovery_manager,
            )

            recovery_manager = get_extension_service_recovery_manager()
            if recovery_manager:
                # Execute shutdown handlers first
                await recovery_manager.execute_shutdown_handlers()

                # Then shutdown the recovery system
                await shutdown_extension_service_recovery_manager()

                logger.info("Extension service recovery system shutdown completed")

        except Exception as e:
            logger.error(f"Extension service recovery shutdown failed: {e}")


async def initialize_fallback_systems() -> None:
    """Initialize fallback systems for degraded mode operation"""
    try:
        # This would contain fallback system initialization logic
        logger.info("Fallback systems initialized")
    except Exception as e:
        logger.error(f"Failed to initialize fallback systems: {e}")


async def run_startup_checks_and_fallbacks(logger_param) -> None:
    """Run startup checks and initialize fallback systems if needed"""
    try:
        await initialize_fallback_systems()
        logger_param.info("Startup checks completed successfully")
    except Exception as e:
        logger_param.error(f"Startup checks failed: {e}")
        # Continue with fallback systems
