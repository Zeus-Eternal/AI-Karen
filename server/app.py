# mypy: ignore-errors
"""
FastAPI application factory for Kari Server.
Creates and configures the FastAPI app with all components.
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# Import all modular components
from .config import Settings
from .logging_setup import configure_logging
from .security import pwd_context, api_key_header, oauth2_scheme, get_ssl_context, require_extension_read, require_background_tasks, require_extension_write, require_extension_admin
from .metrics import initialize_metrics, REQUEST_COUNT, REQUEST_LATENCY, ERROR_COUNT, PROMETHEUS_ENABLED
try:
    from prometheus_client import REGISTRY, generate_latest, CONTENT_TYPE_LATEST
except ImportError:
    REGISTRY = None
from .validation import initialize_validation_framework
from .middleware import configure_middleware
from .performance import load_performance_settings
from .routers import wire_routers
from .startup import create_lifespan, register_startup_tasks
from .database_config import get_database_config, database_lifespan
from .admin_endpoints import register_admin_endpoints
from .health_endpoints import register_health_endpoints
from .debug_endpoints import register_debug_endpoints

logger = logging.getLogger("kari")

# Extension system integration
try:
    from src.extensions.integration import initialize_extensions
    EXTENSIONS_AVAILABLE = True
except ImportError:
    EXTENSIONS_AVAILABLE = False
    logger.warning("Extension system not available")

# Global variables from original main.py
ENABLED_PLUGINS = []
PLUGIN_MAP = {}


def setup_developer_api(app: FastAPI) -> None:
    """Setup developer API endpoints (imported from ui_launchers.backend)"""
    try:
        from ui_launchers.backend.developer_api import setup_developer_api as setup_dev_api
        setup_dev_api(app)
    except ImportError:
        logger.warning("Developer API not available")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    # Load configuration (environment loading is handled in config module)
    settings = Settings()
    environment = settings.environment.lower()
    
    # Configure logging
    configure_logging()
    
    # Load performance configuration
    load_performance_settings(settings)
    
    # Initialize validation framework
    initialize_validation_framework(settings)
    
    # Setup metrics
    initialize_metrics()
    
    # Create lifespan manager with database configuration
    lifespan = create_lifespan(settings)
    
    # Initialize database configuration
    db_config = get_database_config(settings)
    
    # Create FastAPI app
    app = FastAPI(
        title="Kari AI Assistant API",
        description="Advanced AI assistant with multi-modal capabilities",
        version="1.0.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        lifespan=lifespan,
    )
    
    # Configure middleware
    configure_middleware(app, settings, REQUEST_COUNT, REQUEST_LATENCY, ERROR_COUNT)
    
    # Optionally defer router wiring to speed up initial readiness in dev
    # Default to immediate wiring so critical routes (e.g. auth) are available
    # before the first request without requiring special environment flags.
    _defer_wiring = os.getenv("KARI_DEFER_ROUTER_WIRING", "false").lower() in ("1", "true", "yes")
    if _defer_wiring and settings.environment != "production":
        logger.info("⚡ Deferring router wiring to background for faster readiness")
    else:
        # Wire all routers immediately (production/default)
        wire_routers(app, settings)
    
    # Register startup tasks
    register_startup_tasks(app)
    
    # Register shutdown tasks for extension service recovery
    from .startup import register_shutdown_tasks
    register_shutdown_tasks(app)
    
    # Register endpoint groups
    register_admin_endpoints(app, settings)
    register_health_endpoints(app)

    if settings.debug and environment != "production":
        register_debug_endpoints(app, settings)
    else:
        logger.info("Debug endpoints disabled for non-debug or production environments")

    # Setup developer API (non-production only)
    if environment != "production":
        setup_developer_api(app)
    else:
        logger.info("Developer API disabled in production environment")
    
    # Initialize extension system
    if EXTENSIONS_AVAILABLE:
        try:
            # Create a minimal extension router for immediate availability
            from fastapi import APIRouter
            extension_router = APIRouter(prefix="/api/extensions", tags=["extensions"])
            
            @extension_router.get("/")
            async def list_extensions(
                user_context: Dict[str, Any] = Depends(require_extension_read)
            ):
                """List all extensions with proper authentication and tenant isolation."""
                logger.info(f"User {user_context['user_id']} (tenant: {user_context.get('tenant_id', 'default')}) listing extensions")
                
                # Apply tenant isolation - filter extensions based on user's tenant
                tenant_id = user_context.get('tenant_id', 'default')
                user_roles = user_context.get('roles', [])
                
                # Base extensions available to all authenticated users
                extensions = {
                    'analytics-dashboard': {
                        'name': 'analytics-dashboard',
                        'version': '1.0.0',
                        'display_name': 'Analytics Dashboard',
                        'description': 'Sample analytics dashboard extension',
                        'category': 'analytics',
                        'status': 'active',
                        'capabilities': {
                            'provides_ui': True,
                            'provides_api': True,
                            'provides_background_tasks': True,
                            'provides_webhooks': False
                        },
                        'loaded_at': datetime.now(timezone.utc).isoformat(),
                        'error': None,
                        'tenant_access': [tenant_id] if tenant_id != 'system' else ['*']
                    }
                }
                
                # Add admin-only extensions for admin users
                if 'admin' in user_roles:
                    extensions['system-monitor'] = {
                        'name': 'system-monitor',
                        'version': '1.0.0',
                        'display_name': 'System Monitor',
                        'description': 'System monitoring and administration extension',
                        'category': 'admin',
                        'status': 'active',
                        'capabilities': {
                            'provides_ui': True,
                            'provides_api': True,
                            'provides_background_tasks': True,
                            'provides_webhooks': True
                        },
                        'loaded_at': datetime.now(timezone.utc).isoformat(),
                        'error': None,
                        'tenant_access': ['*']
                    }
                
                return {
                    'extensions': extensions,
                    'total': len(extensions),
                    'loaded': len(extensions),
                    'user_context': {
                        'user_id': user_context['user_id'],
                        'tenant_id': tenant_id,
                        'roles': user_roles
                    }
                }
            
            @extension_router.get("/background-tasks/")
            async def list_background_tasks(
                extension_name: Optional[str] = None,
                user_context: Dict[str, Any] = Depends(require_background_tasks)
            ):
                """List background tasks with proper authentication and tenant isolation."""
                logger.info(f"User {user_context['user_id']} (tenant: {user_context.get('tenant_id', 'default')}) listing background tasks")
                
                # Apply tenant isolation for background tasks
                tenant_id = user_context.get('tenant_id', 'default')
                user_roles = user_context.get('roles', [])
                
                # Mock background tasks filtered by tenant and extension
                tasks = []
                
                # Add sample tasks based on user permissions and tenant
                if extension_name is None or extension_name == 'analytics-dashboard':
                    tasks.append({
                        'id': f'analytics_task_{tenant_id}',
                        'name': 'Analytics Data Processing',
                        'extension_name': 'analytics-dashboard',
                        'status': 'running',
                        'tenant_id': tenant_id,
                        'created_by': user_context['user_id'],
                        'created_at': datetime.now(timezone.utc).isoformat(),
                        'next_run': (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
                    })
                
                # Add admin tasks for admin users
                if 'admin' in user_roles and (extension_name is None or extension_name == 'system-monitor'):
                    tasks.append({
                        'id': f'system_monitor_task_{tenant_id}',
                        'name': 'System Health Check',
                        'extension_name': 'system-monitor',
                        'status': 'scheduled',
                        'tenant_id': tenant_id,
                        'created_by': user_context['user_id'],
                        'created_at': datetime.now(timezone.utc).isoformat(),
                        'next_run': (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
                    })
                
                return {
                    'tasks': tasks,
                    'total': len(tasks),
                    'extension_name': extension_name,
                    'tenant_id': tenant_id
                }
            
            @extension_router.post("/background-tasks/")
            async def register_background_task(
                task_data: Dict[str, Any],
                user_context: Dict[str, Any] = Depends(require_background_tasks)
            ):
                """Register a new background task with proper authentication and tenant isolation."""
                logger.info(f"User {user_context['user_id']} (tenant: {user_context.get('tenant_id', 'default')}) registering background task")
                
                # Validate required fields
                required_fields = ['name', 'extension_name']
                missing_fields = [field for field in required_fields if field not in task_data]
                if missing_fields:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing required fields: {', '.join(missing_fields)}"
                    )
                
                # Apply tenant isolation
                tenant_id = user_context.get('tenant_id', 'default')
                task_data['tenant_id'] = tenant_id
                task_data['created_by'] = user_context['user_id']
                task_data['created_at'] = datetime.now(timezone.utc).isoformat()
                
                # Generate task ID with tenant isolation
                task_id = f"{task_data['extension_name']}_{task_data['name']}_{tenant_id}_{user_context['user_id']}"
                task_id = task_id.replace(' ', '_').replace('-', '_').lower()
                
                # Mock task registration (in real implementation, this would interact with extension manager)
                registered_task = {
                    'id': task_id,
                    'name': task_data['name'],
                    'extension_name': task_data['extension_name'],
                    'status': 'registered',
                    'tenant_id': tenant_id,
                    'created_by': user_context['user_id'],
                    'created_at': task_data['created_at'],
                    'schedule': task_data.get('schedule', 'manual'),
                    'config': task_data.get('config', {}),
                    'next_run': None
                }
                
                logger.info(f"Background task registered: {task_id} for tenant {tenant_id}")
                
                return {
                    'task': registered_task,
                    'message': 'Background task registered successfully',
                    'status': 'registered'
                }
            
            @extension_router.get("/admin/status")
            async def get_extension_admin_status(
                api_key: str = Depends(api_key_header),
                user_context: Dict[str, Any] = Depends(require_extension_admin)
            ):
                """Get extension system admin status with API key and admin authentication."""
                # Validate API key for admin operations
                if api_key != settings.secret_key:
                    raise HTTPException(status_code=401, detail="Invalid or missing API key")
                
                logger.info(f"Admin user {user_context['user_id']} accessing extension admin status")
                
                # Return comprehensive extension system status
                return {
                    'extension_system': {
                        'status': 'active',
                        'total_extensions': 2,
                        'active_extensions': 2,
                        'failed_extensions': 0,
                        'background_tasks_running': 1,
                        'last_health_check': datetime.now(timezone.utc).isoformat()
                    },
                    'authentication': {
                        'enabled': settings.extension_auth_enabled,
                        'mode': settings.extension_auth_mode,
                        'token_validation': 'active',
                        'rate_limiting': settings.extension_enable_rate_limiting
                    },
                    'tenant_isolation': {
                        'enabled': True,
                        'active_tenants': ['default', 'dev-tenant'],
                        'isolation_level': 'strict'
                    },
                    'admin_user': {
                        'user_id': user_context['user_id'],
                        'tenant_id': user_context.get('tenant_id', 'system'),
                        'roles': user_context.get('roles', []),
                        'permissions': user_context.get('permissions', [])
                    }
                }
            
            @extension_router.post("/admin/reload")
            async def reload_extension_system(
                api_key: str = Depends(api_key_header),
                user_context: Dict[str, Any] = Depends(require_extension_admin)
            ):
                """Reload extension system with API key and admin authentication."""
                # Validate API key for admin operations
                if api_key != settings.secret_key:
                    raise HTTPException(status_code=401, detail="Invalid or missing API key")
                
                logger.info(f"Admin user {user_context['user_id']} reloading extension system")
                
                try:
                    # Mock extension system reload (in real implementation, this would reload extensions)
                    reload_result = {
                        'status': 'success',
                        'reloaded_extensions': ['analytics-dashboard', 'system-monitor'],
                        'failed_extensions': [],
                        'reload_time': datetime.now(timezone.utc).isoformat(),
                        'admin_user': user_context['user_id']
                    }
                    
                    logger.info(f"Extension system reloaded successfully by {user_context['user_id']}")
                    return reload_result
                    
                except Exception as e:
                    logger.error(f"Extension system reload failed: {e}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Extension system reload failed: {str(e)}"
                    )
            
            app.include_router(extension_router)
            logger.info("Extension system endpoints registered successfully")
            
            # Schedule full extension loading for startup
            async def initialize_extension_system():
                """Initialize the extension system on startup."""
                try:
                    success = await initialize_extensions(
                        app=app,
                        extension_root="extensions",
                        db_session=None,  # Will be injected when database integration is ready
                        plugin_router=None  # Will be injected when plugin orchestrator is ready
                    )
                    if success:
                        logger.info("Extension system initialized successfully")
                        
                        # Initialize extension health monitoring
                        try:
                            from server.extension_health_monitor import initialize_extension_health_monitor
                            
                            # Get the extension manager from the extension system
                            extension_system = getattr(app.state, 'extension_system', None)
                            extension_manager = extension_system.extension_manager if extension_system else None
                            
                            await initialize_extension_health_monitor(extension_manager)
                            logger.info("Extension health monitoring initialized")
                        except Exception as e:
                            logger.warning(f"Extension health monitoring initialization failed: {e}")
                    else:
                        logger.warning("Extension system initialization failed")
                except Exception as e:
                    logger.error(f"Extension system initialization error: {e}")
            
            # Register the startup event
            app.add_event_handler("startup", initialize_extension_system)
            
        except Exception as e:
            logger.error(f"Failed to register extension system: {e}")
    else:
        logger.info("Extension system disabled - not available")
    
    # Add extension system shutdown handler
    @app.on_event("shutdown")
    async def shutdown_extension_health_monitoring():
        """Shutdown extension health monitoring on application shutdown."""
        try:
            from server.extension_health_monitor import shutdown_extension_health_monitor
            await shutdown_extension_health_monitor()
            logger.info("Extension health monitoring shutdown completed")
        except Exception as e:
            logger.warning(f"Extension health monitoring shutdown error: {e}")
    
    # Add compatibility aliases for copilot
    try:
        from ai_karen_engine.api_routes.copilot_routes import (
            copilot_assist,  # type: ignore
            copilot_health,  # type: ignore
        )
        # Accept POST (primary), plus OPTIONS for simple checks
        app.add_api_route(
            "/copilot/assist", copilot_assist, methods=["POST", "OPTIONS"], tags=["copilot-compat"]
        )
        # Health alias for convenience
        app.add_api_route(
            "/copilot/health", copilot_health, methods=["GET"], tags=["copilot-compat"]
        )
        # Log presence of alias for quick diagnosis
        try:
            alias_present = any(getattr(r, "path", "") == "/copilot/assist" for r in app.routes)
            logger.info(f"Copilot legacy alias registered: {alias_present}")
        except Exception:
            pass
    except Exception as e:
        logger.warning(f"Copilot legacy alias not registered: {e}")

    # Proactively register copilot routing actions
    try:
        from ai_karen_engine.integrations.copilotkit.routing_actions import (
            ensure_kire_actions_registered,
        )
        ensure_kire_actions_registered()
    except Exception:
        pass
    
    # Add LLM warmup startup task
    @app.on_event("startup")
    async def _warmup_llm_provider() -> None:
        """Warm up the default LLM provider to reduce first-request latency."""
        import os as _os
        if _os.getenv("WARMUP_LLM", "true").lower() not in ("1", "true", "yes"):
            logger.info("LLM warmup disabled via WARMUP_LLM env")
            return
        try:
            from ai_karen_engine.integrations.llm_registry import LLMRegistry  # type: ignore
            reg = LLMRegistry()
            prov = reg.get_provider("llamacpp")
            if prov is not None:
                try:
                    _ = prov.get_provider_info()  # type: ignore[attr-defined]
                except Exception:
                    pass
                logger.info("LLM warmup completed (llamacpp)")
            else:
                logger.warning("LLM warmup: llamacpp provider not available")
        except Exception as e:
            logger.warning(f"LLM warmup skipped due to error: {e}")
    
    # Add comprehensive health check endpoint
    @app.get("/health", tags=["system"])
    async def health_check():
        """Comprehensive health check with fallback status including extension system"""
        try:
            from datetime import datetime, timezone
            from pathlib import Path
            
            # Check service registry status
            service_status = {}
            try:
                from ai_karen_engine.core.service_registry import ServiceRegistry
                registry = ServiceRegistry()
                report = registry.get_initialization_report()
                service_status = {
                    "total_services": report["summary"]["total_services"],
                    "ready_services": report["summary"]["ready_services"],
                    "degraded_services": report["summary"]["degraded_services"],
                    "error_services": report["summary"]["error_services"]
                }
            except Exception:
                service_status = {"status": "unknown"}
            
            # Check connection health with enhanced database information
            connection_status = {}
            try:
                from ai_karen_engine.services.database_connection_manager import get_database_manager
                from ai_karen_engine.services.redis_connection_manager import get_redis_manager
                
                db_manager = get_database_manager()
                redis_manager = get_redis_manager()
                
                # Get detailed database status
                db_health = await db_config.get_database_health()
                
                connection_status = {
                    "database": {
                        "status": "degraded" if db_manager.is_degraded() else "healthy",
                        "pool_info": db_health.get("pool_info", {}),
                        "configuration": db_health.get("configuration", {}),
                        "connection_failures": db_health.get("connection_failures", 0),
                    },
                    "redis": "degraded" if redis_manager.is_degraded() else "healthy"
                }
            except Exception as e:
                connection_status = {
                    "database": {"status": "unknown", "error": str(e)}, 
                    "redis": "unknown"
                }
            
            # Check extension system health
            extension_status = {}
            try:
                from server.extension_health_monitor import get_extension_health_monitor
                
                extension_monitor = get_extension_health_monitor()
                if extension_monitor:
                    ext_health = await extension_monitor.get_extension_health_for_api()
                    extension_status = {
                        "status": ext_health["status"],
                        "total_extensions": ext_health["extensions"]["total"],
                        "healthy_extensions": ext_health["extensions"]["healthy"],
                        "degraded_extensions": ext_health["extensions"]["degraded"],
                        "unhealthy_extensions": ext_health["extensions"]["unhealthy"],
                        "authentication_healthy": ext_health["supporting_services"]["authentication"]["healthy"],
                        "database_healthy": ext_health["supporting_services"]["database"]["healthy"],
                        "background_tasks_healthy": ext_health["supporting_services"]["background_tasks"]["healthy"]
                    }
                else:
                    extension_status = {"status": "unknown", "monitor_available": False}
            except Exception as e:
                extension_status = {"status": "error", "error": str(e)}
            
            # Check model availability
            model_status = {}
            try:
                models_dir = Path("models")
                gguf_models = list(models_dir.rglob("*.gguf"))
                bin_models = list(models_dir.rglob("*.bin"))
                
                model_status = {
                    "local_models": len(gguf_models) + len(bin_models),
                    "fallback_available": (models_dir / "llama-cpp" / "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf").exists()
                }
            except Exception:
                model_status = {"local_models": 0, "fallback_available": False}
            
            # Check model orchestrator health
            model_orchestrator_status = {}
            try:
                from ai_karen_engine.health.model_orchestrator_health import get_model_orchestrator_health
                health_checker = get_model_orchestrator_health()
                orchestrator_health = await health_checker.check_health()
                model_orchestrator_status = {
                    "status": orchestrator_health.get("status", "unknown"),
                    "registry_healthy": orchestrator_health.get("registry_healthy", False),
                    "storage_healthy": orchestrator_health.get("storage_healthy", False),
                    "plugin_loaded": "model_orchestrator" in ENABLED_PLUGINS,
                    "last_check": orchestrator_health.get("timestamp")
                }
            except Exception as e:
                model_orchestrator_status = {
                    "status": "error",
                    "error": str(e),
                    "plugin_loaded": "model_orchestrator" in ENABLED_PLUGINS
                }
            
            # Determine overall status including extension system
            overall_status = "healthy"
            if connection_status.get("database") == "degraded" or connection_status.get("redis") == "degraded":
                overall_status = "degraded"
            if service_status.get("error_services", 0) > 0:
                overall_status = "degraded"
            if extension_status.get("status") == "degraded":
                overall_status = "degraded"
            if extension_status.get("status") == "unhealthy":
                overall_status = "unhealthy"
            
            return {
                "status": overall_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "environment": settings.environment,
                "version": "1.0.0",
                "services": service_status,
                "connections": connection_status,
                "extension_system": extension_status,
                "models": model_status,
                "model_orchestrator": model_orchestrator_status,
                "plugins": len(ENABLED_PLUGINS),
                "fallback_systems": {
                    "analytics": "active",
                    "error_responses": "active", 
                    "provider_chains": "active",
                    "connection_health": "active",
                    "extension_graceful_degradation": "active"
                }
            }
    
        except Exception as e:
            from datetime import datetime, timezone
            return {
                "status": "error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "environment": settings.environment,
                "version": "1.0.0",
                "error": str(e),
                "fallback_mode": True
            }

    # Background task to wire routers after startup, if deferred
    if _defer_wiring and settings.environment != "production":
        @app.on_event("startup")
        async def _wire_routers_bg() -> None:
            try:
                import asyncio as _asyncio
                # Small delay to allow server to bind
                await _asyncio.sleep(0.1)
                wire_routers(app, settings)
                logger.info("✅ Routers wired in background")
            except Exception as _e:
                logger.warning(f"Deferred router wiring failed: {_e}")
    
    # Add shutdown handler for graceful database cleanup
    @app.on_event("shutdown")
    async def _shutdown_database() -> None:
        """Graceful shutdown of database connections"""
        try:
            logger.info("Starting database shutdown process")
            await db_config.cleanup()
            logger.info("Database shutdown completed successfully")
        except Exception as e:
            logger.error(f"Error during database shutdown: {e}")
    
    # Add metrics endpoint
    @app.get("/metrics", tags=["monitoring"])
    async def metrics(api_key: str = Depends(api_key_header)):
        """Prometheus metrics endpoint requiring X-API-KEY header with extension metrics"""
        if not PROMETHEUS_ENABLED:
            raise HTTPException(
                status_code=501,
                detail="Metrics are not enabled",
            )
        if api_key != settings.secret_key:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")

        # Ensure extension metrics are up-to-date before serving
        try:
            from server.extension_health_monitor import get_extension_health_monitor
            extension_monitor = get_extension_health_monitor()
            if extension_monitor:
                # Force a health check to update metrics
                health = await extension_monitor.check_extension_system_health()
                extension_monitor.update_extension_metrics(health)
        except Exception as e:
            logger.warning(f"Failed to update extension metrics before serving: {e}")

        return Response(
            content=generate_latest(REGISTRY),
            media_type=CONTENT_TYPE_LATEST,
        )

    # Add plugins endpoint
    @app.get("/plugins", tags=["plugins"])
    async def list_plugins():
        """List all plugins with detailed status"""
        return {
            "enabled": sorted(ENABLED_PLUGINS),
            "available": sorted(PLUGIN_MAP.keys()),
            "count": len(PLUGIN_MAP),
        }
    
    # Add database health endpoint
    @app.get("/api/health/database", tags=["system"])
    async def database_health():
        """Database health check endpoint with detailed connection information"""
        try:
            health_info = await db_config.get_database_health()
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "database": health_info
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "database": {
                    "status": "error",
                    "healthy": False,
                    "error": str(e)
                }
            }
    
    # Add database connection test endpoint
    @app.get("/api/health/database/test", tags=["system"])
    async def test_database_connection():
        """Test database connection with timeout"""
        try:
            start_time = datetime.now(timezone.utc)
            success = await db_config.test_database_connection()
            end_time = datetime.now(timezone.utc)
            
            response_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                "timestamp": start_time.isoformat(),
                "connection_test": {
                    "success": success,
                    "response_time_ms": response_time,
                    "timeout_configured": settings.db_connection_timeout,
                }
            }
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "connection_test": {
                    "success": False,
                    "error": str(e),
                    "timeout_configured": settings.db_connection_timeout,
                }
            }
    
    # Add database health monitor endpoint
    @app.get("/api/health/database/monitor", tags=["system"])
    async def database_health_monitor():
        """Get comprehensive database health monitoring information including extension services"""
        try:
            health_monitor = db_config.get_database_health_monitor()
            
            if not health_monitor:
                return {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "monitor": {
                        "status": "not_initialized",
                        "error": "Database health monitor not initialized"
                    }
                }
            
            # Get current health status
            current_health = health_monitor.get_current_health()
            
            # Get pool status
            pool_status = health_monitor.get_pool_status()
            
            # Get metrics history (last 10 entries)
            metrics_history = health_monitor.get_metrics_history()[-10:]
            
            # Get extension service health if available
            extension_health = {}
            try:
                from server.enhanced_database_health_monitor import get_enhanced_database_health_monitor
                enhanced_monitor = get_enhanced_database_health_monitor()
                if enhanced_monitor:
                    extension_health = await enhanced_monitor.get_current_health_with_extension_focus()
            except Exception as e:
                logger.warning(f"Failed to get extension database health: {e}")
                extension_health = {"error": str(e)}
            
            # Get detailed extension performance metrics for database monitoring
            extension_performance_metrics = {}
            try:
                from server.extension_health_monitor import get_extension_health_monitor
                extension_monitor = get_extension_health_monitor()
                if extension_monitor:
                    # Get performance metrics for database-dependent extensions
                    performance_data = await extension_monitor.get_database_performance_metrics()
                    extension_performance_metrics = {
                        "database_query_performance": performance_data.get("database_queries", {}),
                        "connection_pool_usage": performance_data.get("connection_usage", {}),
                        "background_task_database_load": performance_data.get("background_task_load", {}),
                        "extension_database_errors": performance_data.get("database_errors", {}),
                        "database_dependent_extensions_count": performance_data.get("dependent_extensions_count", 0),
                        "total_database_operations_per_minute": performance_data.get("operations_per_minute", 0)
                    }
            except Exception as e:
                logger.warning(f"Failed to get extension performance metrics for database monitoring: {e}")
                extension_performance_metrics = {"error": str(e)}
            
            # Get comprehensive extension system health for database monitoring
            extension_system_health = {}
            try:
                from server.extension_health_monitor import get_extension_health_monitor
                extension_monitor = get_extension_health_monitor()
                if extension_monitor:
                    ext_health = await extension_monitor.get_extension_health_for_api()
                    extension_system_health = {
                        "status": ext_health["status"],
                        "total_extensions": ext_health["extensions"]["total"],
                        "healthy_extensions": ext_health["extensions"]["healthy"],
                        "degraded_extensions": ext_health["extensions"]["degraded"],
                        "unhealthy_extensions": ext_health["extensions"]["unhealthy"],
                        "database_dependent_extensions": [
                            name for name, details in ext_health["extensions"]["details"].items()
                            if details.get("background_tasks_active", 0) > 0 or 
                               details.get("error", "").lower().find("database") != -1
                        ],
                        "authentication_healthy": ext_health["supporting_services"]["authentication"]["healthy"],
                        "background_tasks_healthy": ext_health["supporting_services"]["background_tasks"]["healthy"],
                        "uptime_seconds": ext_health["uptime_seconds"]
                    }
                else:
                    extension_system_health = {"status": "unknown", "monitor_not_available": True}
            except Exception as e:
                logger.warning(f"Failed to get extension system health for database monitoring: {e}")
                extension_system_health = {"status": "error", "error": str(e)}
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "monitor": {
                    "status": current_health.status.value,
                    "is_connected": current_health.is_connected,
                    "response_time_ms": current_health.response_time,
                    "error_count": current_health.error_count,
                    "consecutive_failures": current_health.consecutive_failures,
                    "last_check": current_health.last_check.isoformat(),
                    "last_success": current_health.last_success.isoformat() if current_health.last_success else None,
                    "last_error": current_health.last_error,
                    "degraded_features": current_health.degraded_features,
                    "recovery_attempts": current_health.recovery_attempts,
                    "next_recovery_attempt": current_health.next_recovery_attempt.isoformat() if current_health.next_recovery_attempt else None,
                    "metadata": current_health.metadata,
                },
                "pool_status": pool_status,
                "extension_services": extension_health,
                "extension_system": extension_system_health,
                "extension_performance": extension_performance_metrics,
                "metrics_history": [
                    {
                        "timestamp": m.timestamp.isoformat(),
                        "connection_count": m.connection_count,
                        "active_connections": m.active_connections,
                        "idle_connections": m.idle_connections,
                        "response_time_ms": m.response_time_ms,
                        "query_success_rate": m.query_success_rate,
                        "error_count": m.error_count,
                        "pool_status": m.pool_status.value,
                    }
                    for m in metrics_history
                ],
                "configuration": {
                    "health_check_interval": settings.db_health_check_interval,
                    "max_connection_failures": settings.db_max_connection_failures,
                    "connection_retry_delay": settings.db_connection_retry_delay,
                    "connection_timeout": settings.db_connection_timeout,
                    "query_timeout": settings.db_query_timeout,
                }
            }
            
        except Exception as e:
            logger.error(f"Database health monitor endpoint failed: {e}")
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "monitor": {
                    "status": "error",
                    "error": str(e)
                }
            }
    
    # Add degraded mode status endpoint
    @app.get("/api/health/degraded-mode", tags=["system"])
    async def degraded_mode_status():
        """Compatibility proxy that forwards to the canonical health router."""

        try:
            from ai_karen_engine.api_routes.health import (
                degraded_mode_status_compat,
            )

            payload = await degraded_mode_status_compat()
            
            # Enhance payload with extension system information
            try:
                from server.extension_health_monitor import get_extension_health_monitor
                extension_monitor = get_extension_health_monitor()
                if extension_monitor:
                    ext_health = await extension_monitor.get_extension_health_for_api()
                    payload["extension_system"] = {
                        "status": ext_health["status"],
                        "total_extensions": ext_health["extensions"]["total"],
                        "healthy_extensions": ext_health["extensions"]["healthy"],
                        "degraded_extensions": ext_health["extensions"]["degraded"],
                        "unhealthy_extensions": ext_health["extensions"]["unhealthy"],
                        "authentication_healthy": ext_health["supporting_services"]["authentication"]["healthy"],
                        "database_healthy": ext_health["supporting_services"]["database"]["healthy"],
                        "background_tasks_healthy": ext_health["supporting_services"]["background_tasks"]["healthy"],
                        "degraded_extension_names": [
                            name for name, details in ext_health["extensions"]["details"].items()
                            if details["status"] in ["degraded", "unhealthy"]
                        ],
                        "uptime_seconds": ext_health["uptime_seconds"]
                    }
                    
                    # Update degraded mode status based on extension health
                    if ext_health["status"] in ["degraded", "unhealthy"]:
                        payload["degraded_mode"] = True
                        payload["is_active"] = True
                        if "degraded_components" not in payload:
                            payload["degraded_components"] = []
                        if ext_health["status"] == "unhealthy":
                            payload["degraded_components"].append("extension_system")
                        elif ext_health["status"] == "degraded":
                            payload["degraded_components"].append("extension_system_partial")
                else:
                    payload["extension_system"] = {
                        "status": "unknown",
                        "monitor_available": False
                    }
            except Exception as e:
                logger.warning(f"Failed to enhance degraded mode with extension info: {e}")
                payload["extension_system"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            return payload
        except Exception as exc:
            logger.warning("Degraded mode proxy fallback due to error: %s", exc)
            
            # Get extension system status for degraded mode reporting
            extension_degraded_info = {}
            try:
                from server.extension_health_monitor import get_extension_health_monitor
                extension_monitor = get_extension_health_monitor()
                if extension_monitor:
                    ext_health = await extension_monitor.get_extension_health_for_api()
                    extension_degraded_info = {
                        "extension_system_status": ext_health["status"],
                        "total_extensions": ext_health["extensions"]["total"],
                        "healthy_extensions": ext_health["extensions"]["healthy"],
                        "degraded_extensions": ext_health["extensions"]["degraded"],
                        "unhealthy_extensions": ext_health["extensions"]["unhealthy"],
                        "extension_authentication_healthy": ext_health["supporting_services"]["authentication"]["healthy"],
                        "extension_database_healthy": ext_health["supporting_services"]["database"]["healthy"],
                        "extension_background_tasks_healthy": ext_health["supporting_services"]["background_tasks"]["healthy"],
                        "degraded_extension_names": [
                            name for name, details in ext_health["extensions"]["details"].items()
                            if details["status"] in ["degraded", "unhealthy"]
                        ]
                    }
                else:
                    extension_degraded_info = {
                        "extension_system_status": "unknown",
                        "extension_monitor_available": False
                    }
            except Exception as e:
                logger.warning(f"Failed to get extension status for degraded mode: {e}")
                extension_degraded_info = {
                    "extension_system_status": "error",
                    "extension_error": str(e)
                }
            
            return {
                "degraded_mode": True,
                "is_active": True,
                "ai_status": "degraded",
                "reason": "health_check_failed",
                "failed_providers": [],
                "degraded_components": ["health_router"],
                "core_helpers_available": {
                    "fallback_responses": True,
                    "local_fallback_ready": False,
                },
                "fallback_systems_active": True,
                "extension_system": extension_degraded_info,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(exc),
            }
    
    logger.info("FastAPI application created and configured successfully")
    return app
