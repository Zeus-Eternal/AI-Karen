"""
Platform Monitoring Startup Integration

Integration with FastAPI application startup and shutdown events for
the entire platform monitoring system including both platform and extension monitoring.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI

from .metrics_service import get_metrics_service
from .structured_logging_service import get_structured_logging_service
from .correlation_service import get_correlation_service
from .extensions.startup_integration import (
    setup_monitoring_app as setup_extension_monitoring_app,
    monitoring_lifespan as extension_monitoring_lifespan,
    get_monitoring_router as get_extension_monitoring_router,
    get_monitoring_middleware as get_extension_monitoring_middleware,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def platform_monitoring_lifespan(app: FastAPI):
    """FastAPI lifespan context manager for platform monitoring system."""

    # Startup
    try:
        logger.info("Starting platform monitoring system...")

        # Initialize platform monitoring services
        metrics_service = get_metrics_service()
        logging_service = get_structured_logging_service()
        correlation_service = get_correlation_service()

        # Initialize platform monitoring services
        await metrics_service.initialize()
        await logging_service.initialize()
        await correlation_service.initialize()

        logger.info("Platform monitoring system started successfully")

    except Exception as e:
        logger.error(f"Failed to start platform monitoring system: {e}")
        # Don't fail the entire application if monitoring fails

    # Start extension monitoring
    try:
        async with extension_monitoring_lifespan(app):
            yield
    except Exception as e:
        logger.error(f"Extension monitoring error: {e}")
        yield

    # Shutdown
    try:
        logger.info("Shutting down platform monitoring system...")

        # Shutdown platform monitoring services
        if metrics_service:
            await metrics_service.shutdown()
        if logging_service:
            await logging_service.shutdown()
        if correlation_service:
            await correlation_service.shutdown()

        logger.info("Platform monitoring system shutdown complete")
    except Exception as e:
        logger.error(f"Error during platform monitoring shutdown: {e}")


def setup_platform_monitoring_app(
    app: FastAPI, config: Dict[str, Any] = None
) -> FastAPI:
    """Setup platform monitoring for an existing FastAPI application."""

    # Setup extension monitoring
    app = setup_extension_monitoring_app(app, config)

    logger.info("Platform monitoring integration configured")
    return app


def create_platform_monitoring_app(config: Dict[str, Any] = None) -> FastAPI:
    """Create a new FastAPI application with platform monitoring enabled."""

    # Create FastAPI app with platform monitoring lifespan
    app = FastAPI(
        title="Kari AI Platform Monitoring",
        description="Platform monitoring and alerting system for Kari AI",
        version="1.0.0",
        lifespan=platform_monitoring_lifespan,
    )

    # Add monitoring middleware
    from .extensions.startup_integration import get_monitoring_middleware

    MonitoringMiddleware = get_monitoring_middleware()
    if MonitoringMiddleware:
        app.add_middleware(MonitoringMiddleware)

    # Include monitoring routes
    from .extensions.startup_integration import get_monitoring_router

    monitoring_router = get_monitoring_router()
    if monitoring_router:
        app.include_router(monitoring_router)

    # Add platform health check endpoint
    @app.get("/health/platform")
    async def platform_health_check():
        """Platform health check endpoint."""
        try:
            metrics_service = get_metrics_service()
            logging_service = get_structured_logging_service()
            correlation_service = get_correlation_service()

            return {
                "status": "healthy",
                "platform_monitoring": {
                    "metrics_initialized": metrics_service is not None,
                    "logging_initialized": logging_service is not None,
                    "correlation_initialized": correlation_service is not None,
                },
                "last_updated": metrics_service.last_updated()
                if metrics_service
                else None,
            }
        except Exception as e:
            logger.error(f"Platform health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    # Add extension health check endpoint
    from .extensions.integration import monitoring_integration

    @app.get("/health/extensions")
    async def extensions_health_check():
        """Extensions health check endpoint."""
        try:
            status = monitoring_integration.get_monitoring_status()
            return {
                "status": "healthy" if status.get("initialized") else "unhealthy",
                "extension_monitoring": status,
            }
        except Exception as e:
            logger.error(f"Extensions health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    return app


def get_platform_monitoring_status() -> Dict[str, Any]:
    """Get overall platform monitoring status."""
    try:
        metrics_service = get_metrics_service()
        logging_service = get_structured_logging_service()
        correlation_service = get_correlation_service()

        platform_status = {
            "platform": {
                "metrics": {
                    "initialized": metrics_service is not None,
                    "status": "active" if metrics_service else "inactive",
                },
                "logging": {
                    "initialized": logging_service is not None,
                    "status": "active" if logging_service else "inactive",
                },
                "correlation": {
                    "initialized": correlation_service is not None,
                    "status": "active" if correlation_service else "inactive",
                },
            }
        }

        # Get extension monitoring status
        from .extensions.integration import monitoring_integration

        extension_status = monitoring_integration.get_monitoring_status()
        platform_status["extensions"] = extension_status

        # Overall health
        all_healthy = all(
            [
                platform_status["platform"]["metrics"]["initialized"],
                platform_status["platform"]["logging"]["initialized"],
                platform_status["platform"]["correlation"]["initialized"],
                extension_status.get("initialized", False),
            ]
        )

        platform_status["overall_health"] = "healthy" if all_healthy else "degraded"
        platform_status["timestamp"] = (
            __import__("datetime").datetime.utcnow().isoformat()
        )

        return platform_status

    except Exception as e:
        logger.error(f"Failed to get platform monitoring status: {e}")
        return {
            "overall_health": "error",
            "error": str(e),
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }


# Decorator for automatic platform request monitoring
def monitor_platform_endpoint(endpoint_name: str = None):
    """Decorator to automatically monitor endpoint performance."""
    from .extensions.startup_integration import monitor_endpoint

    return monitor_endpoint(endpoint_name)


# Context manager for monitoring platform operations
@asynccontextmanager
async def monitor_platform_operation(
    operation_name: str, service_name: str = "platform_service"
):
    """Context manager to monitor arbitrary platform operations."""
    import time

    start_time = time.time()
    status = "healthy"

    try:
        from .extensions.integration import record_service_health

        yield
    except Exception as e:
        status = "unhealthy"
        logger.error(f"Platform operation {operation_name} failed: {e}")
        raise
    finally:
        response_time = time.time() - start_time
        from .extensions.integration import record_service_health

        record_service_health(service_name, status, response_time)
