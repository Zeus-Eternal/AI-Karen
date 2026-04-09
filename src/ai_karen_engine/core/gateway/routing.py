"""
Routing setup for AI Karen FastAPI gateway.
"""

import os
import importlib
import pkgutil
from typing import Optional

try:
    from fastapi import FastAPI, APIRouter
    from fastapi.responses import JSONResponse, PlainTextResponse
except ImportError:
    FastAPI = object
    APIRouter = object
    JSONResponse = object
    PlainTextResponse = object

from ai_karen_engine.core.services import ServiceContainer
from ai_karen_engine.core.logging import get_logger

logger = get_logger(__name__)


def setup_health_routes(app: FastAPI, service_container: ServiceContainer) -> None:
    """
    Setup health check routes.

    Args:
        app: FastAPI application
        service_container: Service container
    """

    @app.get("/health", response_class=JSONResponse, tags=["Health"])
    async def health_check():
        """Comprehensive health check endpoint."""
        try:
            # Get service health information
            service_health = service_container.get_service_health()

            # Determine overall health
            all_healthy = all(
                service["status"] in ["running", "ready"]
                for service in service_health.values()
            )

            return {
                "status": "healthy" if all_healthy else "unhealthy",
                "version": os.getenv("KAREN_VERSION", "1.0.0"),
                "environment": os.getenv("KAREN_ENV", "development"),
                "services": service_health,
                "timestamp": "2025-01-19T20:00:00Z",  # This would be dynamic in real implementation
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": "2025-01-19T20:00:00Z",
                },
            )

    @app.get("/livez", response_class=PlainTextResponse, tags=["Health"])
    async def liveness_probe():
        """Kubernetes liveness probe endpoint."""
        return "ok"

    @app.get("/readyz", response_class=PlainTextResponse, tags=["Health"])
    async def readiness_probe():
        """Kubernetes readiness probe endpoint."""
        try:
            # Check if critical services are ready
            service_health = service_container.get_service_health()
            critical_services_ready = all(
                service["status"] in ["running", "ready"]
                for service_name, service in service_health.items()
                if service_name
                in ["ai_orchestrator", "memory_service"]  # Define critical services
            )

            if critical_services_ready:
                return "ready"
            else:
                return PlainTextResponse("not ready", status_code=503)

        except Exception:
            return PlainTextResponse("not ready", status_code=503)


def setup_info_routes(app: FastAPI) -> None:
    """
    Setup information routes.

    Args:
        app: FastAPI application
    """

    @app.get("/", response_class=JSONResponse, tags=["Info"])
    async def root():
        """Root endpoint with API information."""
        return {
            "service": "AI Karen Engine",
            "message": "Welcome to the AI Karen Engine API Gateway",
            "version": os.getenv("KAREN_VERSION", "1.0.0"),
            "docs": "/docs",
            "health": "/health",
            "metrics": "/metrics",
        }

    @app.get("/info", response_class=JSONResponse, tags=["Info"])
    async def info():
        """Detailed service information."""
        return {
            "name": "AI Karen Engine",
            "version": os.getenv("KAREN_VERSION", "1.0.0"),
            "environment": os.getenv("KAREN_ENV", "development"),
            "debug": os.getenv("KAREN_DEBUG", "false").lower() == "true",
            "features": {
                "ai_orchestration": True,
                "memory_management": True,
                "plugin_execution": True,
                "tool_abstraction": True,
                "conversation_management": True,
                "analytics": True,
            },
        }


def setup_metrics_routes(app: FastAPI) -> None:
    """
    Setup metrics routes.

    Args:
        app: FastAPI application
    """
    try:
        from prometheus_client import (
            make_asgi_app,
            generate_latest,
            CONTENT_TYPE_LATEST,
        )

        # Check if app has mount method (real FastAPI vs stub)
        if hasattr(app, "mount"):
            # Mount Prometheus metrics
            metrics_app = make_asgi_app()
            app.mount("/metrics", metrics_app)
            logger.info("Prometheus metrics endpoint mounted at /metrics")
        else:
            # Fallback for stub
            @app.get("/metrics", response_class=PlainTextResponse, tags=["Metrics"])
            async def prometheus_metrics():
                """Prometheus metrics endpoint."""
                return generate_latest()

    except ImportError:
        logger.info("Prometheus client not available, skipping metrics endpoint")

        # Provide basic metrics endpoint
        @app.get("/metrics", response_class=PlainTextResponse, tags=["Metrics"])
        async def basic_metrics():
            """Basic metrics endpoint when Prometheus is not available."""
            return "# Prometheus client not available\n# Install prometheus_client for full metrics support\n"


def discover_and_mount_api_routes(app: FastAPI) -> None:
    """
    Discover and mount API routes from the api_routes package.

    Args:
        app: FastAPI application
    """
    try:
        from ai_karen_engine import api_routes

        # Iterate through all modules in api_routes
        for loader, name, is_pkg in pkgutil.iter_modules(api_routes.__path__):
            try:
                module = importlib.import_module(f"ai_karen_engine.api_routes.{name}")

                # Look for router in the module
                router = getattr(module, "router", None)
                if isinstance(router, APIRouter) and hasattr(router, "routes"):
                    router_prefix = getattr(router, "prefix", "")

                    if router_prefix:
                        # Router already has a prefix
                        if router_prefix.startswith("/api/"):
                            # Router prefix already includes /api/, mount directly
                            route_prefix = ""
                            logger.info(
                                f"Router {name} has /api/ prefix, mounting directly: {router_prefix}"
                            )
                        elif (
                            name == "plugin_management" and router_prefix == "/plugins"
                        ):
                            # Special case for plugin management - mount as /api/plugins
                            route_prefix = "/api"
                            # Keep router_prefix as "/plugins"
                            logger.info(
                                f"Special case: mounting plugin_management as /api/plugins"
                            )
                        else:
                            # Router has a relative prefix, mount under /api
                            route_prefix = "/api"
                            logger.info(
                                f"Router {name} has prefix {router_prefix}, mounting under /api"
                            )
                    else:
                        # No prefix, derive one from module name
                        base_name = name.replace("_routes", "").replace("_api", "")

                        # Pluralize common resource names to match frontend conventions
                        plural_resources = [
                            "persona",
                            "conversation",
                            "plugin",
                            "provider",
                            "tool",
                            "plan",
                            "user",
                        ]
                        if base_name in plural_resources:
                            base_name = f"{base_name}s"

                        route_prefix = f"/api/{base_name}"
                        logger.info(
                            f"Auto-assigning prefix {route_prefix} to router from {name}"
                        )

                    app.include_router(router, prefix=route_prefix, tags=[name])
                    final_prefix = (
                        route_prefix + router_prefix if route_prefix else router_prefix
                    )
                    logger.info(f"Mounted API router: {final_prefix} (from {name})")
                    # Log individual routes for debugging
                    for route in router.routes:
                        route_path = getattr(route, "path", "unknown")
                        route_methods = getattr(route, "methods", ["unknown"])
                        logger.info(
                            f"  Route: {route_methods} {final_prefix}/{route_path}"
                        )

                # Mount optional public_router when present (e.g., provider public endpoints)
                public_router = getattr(module, "public_router", None)
                if isinstance(public_router, APIRouter) and hasattr(
                    public_router, "routes"
                ):
                    # Special-case provider public routes so they live under /api/public/providers/...
                    if name == "provider_routes":
                        app.include_router(
                            public_router,
                            prefix="/api/public/providers",
                            tags=["public-providers"],
                        )
                        logger.info(
                            "Mounted public provider router: /api/public/providers"
                        )
                    else:
                        # Fallback: mount under /api/public/<module>
                        app.include_router(public_router, prefix=f"/api/public/{name}")
                        logger.info(f"Mounted public router: /api/public/{name}")

            except Exception as e:
                logger.error(f"Failed to mount API router {name}: {e}")

    except ImportError:
        logger.warning("No api_routes package found")


def discover_and_mount_plugin_routes(app: FastAPI) -> None:
    """
    Discover and mount plugin routes.
    """
    try:
        from extensions.core import get_plugin_router

        router = get_plugin_router()
        # Get dynamic FastAPI router from the modular runtime
        api_router = router.get_api_router()
        app.include_router(api_router, prefix="/plugins", tags=["plugins"])
        logger.info("Mounted dynamic plugin API router at /plugins")

    except Exception as e:
        logger.error(f"Failed to mount plugin router: {e}")


def discover_and_mount_plugin_ui(app: FastAPI) -> None:
    """
    Discover and mount static UI assets for all plugins.
    Allows plugins to serve their own modern frontends.
    """
    try:
        from fastapi.staticfiles import StaticFiles
        from extensions.core import get_plugin_manager

        manager = get_plugin_manager()
        registry = manager.registry

        for plugin_id, record in registry.get_all_manifests().items():
            ui_path = record.dir_path / "ui"
            if ui_path.exists() and ui_path.is_dir():
                mount_path = f"/extensions/{plugin_id}/ui"
                app.mount(
                    mount_path,
                    StaticFiles(directory=str(ui_path), html=True),
                    name=f"ui_{plugin_id}",
                )
                logger.info(f"Mounted UI for plugin '{plugin_id}' at {mount_path}")

    except Exception as e:
        logger.error(f"Failed to mount plugin UIs: {e}")


def setup_service_routes(app: FastAPI, service_container: ServiceContainer) -> None:
    """
    Setup routes for service management.

    Args:
        app: FastAPI application
        service_container: Service container
    """

    @app.get("/services", response_class=JSONResponse, tags=["Services"])
    async def list_services():
        """List all registered services."""
        try:
            services = service_container.get_all_services()
            return {
                "services": [
                    {
                        "name": name,
                        "status": service.status.value,
                        "health": service.health.dict(),
                    }
                    for name, service in services.items()
                ]
            }
        except Exception as e:
            logger.error(f"Failed to list services: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to list services", "detail": str(e)},
            )

    @app.get("/services/{service_name}", response_class=JSONResponse, tags=["Services"])
    async def get_service_info(service_name: str):
        """Get information about a specific service."""
        try:
            service = service_container.get_service(service_name)
            return {
                "name": service.name,
                "status": service.status.value,
                "health": service.health.dict(),
                "metrics": service.get_metrics(),
                "config": service.config.dict(),
            }
        except ValueError:
            return JSONResponse(
                status_code=404,
                content={"error": "Service not found", "service_name": service_name},
            )
        except Exception as e:
            logger.error(f"Failed to get service info for {service_name}: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to get service info", "detail": str(e)},
            )


def setup_routing(app: FastAPI, service_container: ServiceContainer) -> None:
    """
    Setup all routing for the FastAPI application.

    Args:
        app: FastAPI application
        service_container: Service container
    """
    logger.info("Setting up routing")

    # Setup core routes
    setup_health_routes(app, service_container)
    setup_info_routes(app)
    setup_metrics_routes(app)
    setup_service_routes(app, service_container)

    # Discover and mount API routes
    discover_and_mount_api_routes(app)

    # Discover and mount plugin routes & UI
    discover_and_mount_plugin_routes(app)
    discover_and_mount_plugin_ui(app)

    logger.info("Routing setup completed")
