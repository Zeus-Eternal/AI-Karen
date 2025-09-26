# mypy: ignore-errors
"""
FastAPI application factory for Kari Server.
Creates and configures the FastAPI app with all components.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Response
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# Import all modular components
from .config import Settings
from .logging_setup import configure_logging
from .security import pwd_context, api_key_header, oauth2_scheme, get_ssl_context
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
from .admin_endpoints import register_admin_endpoints
from .health_endpoints import register_health_endpoints
from .debug_endpoints import register_debug_endpoints

logger = logging.getLogger("kari")

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
    
    # Configure logging
    configure_logging()
    
    # Load performance configuration
    load_performance_settings(settings)
    
    # Initialize validation framework
    initialize_validation_framework(settings)
    
    # Setup metrics
    initialize_metrics()
    
    # Create lifespan manager
    lifespan = create_lifespan(settings)
    
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
    
    # Register endpoint groups
    register_admin_endpoints(app, settings)
    register_health_endpoints(app)
    register_debug_endpoints(app, settings)
    
    # Setup developer API
    setup_developer_api(app)
    
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
        """Comprehensive health check with fallback status"""
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
            
            # Check connection health
            connection_status = {}
            try:
                from ai_karen_engine.services.database_connection_manager import get_database_manager
                from ai_karen_engine.services.redis_connection_manager import get_redis_manager
                
                db_manager = get_database_manager()
                redis_manager = get_redis_manager()
                
                connection_status = {
                    "database": "degraded" if db_manager.is_degraded() else "healthy",
                    "redis": "degraded" if redis_manager.is_degraded() else "healthy"
                }
            except Exception:
                connection_status = {"database": "unknown", "redis": "unknown"}
            
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
            
            # Determine overall status
            overall_status = "healthy"
            if connection_status.get("database") == "degraded" or connection_status.get("redis") == "degraded":
                overall_status = "degraded"
            if service_status.get("error_services", 0) > 0:
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "environment": settings.environment,
                "version": "1.0.0",
                "services": service_status,
                "connections": connection_status,
                "models": model_status,
                "model_orchestrator": model_orchestrator_status,
                "plugins": len(ENABLED_PLUGINS),
                "fallback_systems": {
                    "analytics": "active",
                    "error_responses": "active", 
                    "provider_chains": "active",
                    "connection_health": "active"
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
    
    # Add metrics endpoint
    @app.get("/metrics", tags=["monitoring"])
    async def metrics(api_key: str = Depends(api_key_header)):
        """Prometheus metrics endpoint requiring X-API-KEY header"""
        if not PROMETHEUS_ENABLED:
            raise HTTPException(
                status_code=501,
                detail="Metrics are not enabled",
            )
        if api_key != settings.secret_key:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")

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
    
    # Add degraded mode status endpoint
    @app.get("/api/health/degraded-mode", tags=["system"])
    async def degraded_mode_status():
        """Check if system is running in degraded mode"""
        try:
            from datetime import datetime, timezone
            from pathlib import Path
            
            # Check various system components for degraded mode
            degraded_components = []
            
            # Check database
            try:
                from ai_karen_engine.services.database_connection_manager import get_database_manager
                db_manager = get_database_manager()
                if db_manager.is_degraded():
                    degraded_components.append("database")
            except Exception:
                degraded_components.append("database")
            
            # Check Redis
            try:
                from ai_karen_engine.services.redis_connection_manager import get_redis_manager
                redis_manager = get_redis_manager()
                if redis_manager.is_degraded():
                    degraded_components.append("redis")
            except Exception:
                degraded_components.append("redis")
            
            # Check AI providers - but consider local models as available
            failed_providers = []
            try:
                from ai_karen_engine.services.provider_registry import get_provider_registry_service
                provider_service = get_provider_registry_service()
                system_status = provider_service.get_system_status()
                
                # Check if we have local models available
                models_dir = Path("models")
                tinyllama_available = (models_dir / "llama-cpp" / "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf").exists()
                
                # Check spaCy availability
                spacy_available = False
                try:
                    import spacy
                    nlp = spacy.load("en_core_web_sm")
                    spacy_available = True
                except:
                    pass
                
                # Only consider degraded if NO providers AND NO local models
                if system_status["available_providers"] == 0 and not (tinyllama_available or spacy_available):
                    degraded_components.append("ai_providers")
                    failed_providers = system_status.get("failed_providers", [])
                elif system_status["available_providers"] == 0:
                    # We have local models, so just note the failed remote providers
                    failed_providers = system_status.get("failed_providers", [])
                    
            except Exception:
                # Check if local models are available as fallback
                try:
                    models_dir = Path("models")
                    tinyllama_available = (models_dir / "llama-cpp" / "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf").exists()
                    
                    import spacy
                    nlp = spacy.load("en_core_web_sm")
                    spacy_available = True
                    
                    # Only degraded if no local models
                    if not (tinyllama_available or spacy_available):
                        degraded_components.append("ai_providers")
                        failed_providers = ["unknown"]
                except:
                    degraded_components.append("ai_providers")
                    failed_providers = ["unknown"]
            
            is_degraded = len(degraded_components) > 0
            
            # Determine degraded mode reason
            reason = None
            if is_degraded:
                if "ai_providers" in degraded_components and "database" in degraded_components:
                    reason = "all_providers_failed"
                elif "database" in degraded_components:
                    reason = "network_issues"
                elif "ai_providers" in degraded_components:
                    reason = "all_providers_failed"
                else:
                    reason = "resource_exhaustion"
            
            return {
                "degraded_mode": is_degraded,
                "reason": reason,
                "degraded_components": degraded_components,
                "failed_providers": failed_providers,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "fallback_systems_active": True
            }
            
        except Exception as e:
            from datetime import datetime, timezone
            return {
                "degraded_mode": True,
                "reason": "system_error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "fallback_systems_active": True
            }
    
    logger.info("FastAPI application created and configured successfully")
    return app
