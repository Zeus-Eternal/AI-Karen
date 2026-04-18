"""
Extension Monitoring Startup Integration

Integration with FastAPI application startup and shutdown events.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI

from .integration import monitoring_integration
from .environment_config import get_config_for_environment, validate_config
from .dashboard_api import monitoring_router, MonitoringMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def monitoring_lifespan(app: FastAPI):
    """FastAPI lifespan context manager for monitoring system."""
    
    # Startup
    try:
        logger.info("Starting extension monitoring system...")
        
        # Get configuration
        config = get_config_for_environment()
        
        # Validate configuration
        validate_config(config)
        
        # Initialize monitoring
        await monitoring_integration.initialize(config)
        
        logger.info("Extension monitoring system started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start monitoring system: {e}")
        # Don't fail the entire application if monitoring fails
    
    yield
    
    # Shutdown
    try:
        logger.info("Shutting down extension monitoring system...")
        await monitoring_integration.shutdown()
        logger.info("Extension monitoring system shutdown complete")
    except Exception as e:
        logger.error(f"Error during monitoring shutdown: {e}")


def setup_monitoring_app(app: FastAPI, config: Dict[str, Any] = None) -> FastAPI:
    """Setup monitoring for an existing FastAPI application."""
    
    # Add monitoring middleware
    app.add_middleware(MonitoringMiddleware)
    
    # Include monitoring routes
    app.include_router(monitoring_router)
    
    # Add startup and shutdown events if lifespan is not used
    @app.on_event("startup")
    async def startup_monitoring():
        try:
            if config is None:
                monitoring_config = get_config_for_environment()
            else:
                monitoring_config = config
            
            validate_config(monitoring_config)
            await monitoring_integration.initialize(monitoring_config)
            logger.info("Monitoring system initialized on startup")
        except Exception as e:
            logger.error(f"Failed to initialize monitoring on startup: {e}")
    
    @app.on_event("shutdown")
    async def shutdown_monitoring():
        try:
            await monitoring_integration.shutdown()
            logger.info("Monitoring system shutdown on application shutdown")
        except Exception as e:
            logger.error(f"Error shutting down monitoring: {e}")
    
    return app


def create_monitoring_app(config: Dict[str, Any] = None) -> FastAPI:
    """Create a new FastAPI application with monitoring enabled."""
    
    # Create FastAPI app with monitoring lifespan
    app = FastAPI(
        title="Extension Monitoring API",
        description="Monitoring and alerting system for extension authentication and services",
        version="1.0.0",
        lifespan=monitoring_lifespan
    )
    
    # Add monitoring middleware
    app.add_middleware(MonitoringMiddleware)
    
    # Include monitoring routes
    app.include_router(monitoring_router)
    
    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        status = monitoring_integration.get_monitoring_status()
        return {
            "status": "healthy" if status["initialized"] else "unhealthy",
            "monitoring": status
        }
    
    return app


# Decorator for automatic request monitoring
def monitor_endpoint(endpoint_name: str = None):
    """Decorator to automatically monitor endpoint performance."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            import time
            from .integration import record_api_request
            
            # Extract endpoint name
            name = endpoint_name or getattr(func, '__name__', 'unknown')
            method = 'GET'  # Default, could be enhanced to detect actual method
            
            start_time = time.time()
            status_code = 200
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = 500
                raise
            finally:
                response_time = time.time() - start_time
                record_api_request(name, method, status_code, response_time)
        
        return wrapper
    return decorator


# Context manager for monitoring code blocks
@asynccontextmanager
async def monitor_operation(operation_name: str, service_name: str = "extension_service"):
    """Context manager to monitor arbitrary operations."""
    import time
    from .integration import record_service_health
    
    start_time = time.time()
    status = "healthy"
    
    try:
        yield
    except Exception as e:
        status = "unhealthy"
        logger.error(f"Operation {operation_name} failed: {e}")
        raise
    finally:
        response_time = time.time() - start_time
        record_service_health(service_name, status, response_time)


# Utility functions for manual integration
async def initialize_monitoring_with_retry(config: Dict[str, Any] = None, max_retries: int = 3):
    """Initialize monitoring with retry logic."""
    
    if config is None:
        config = get_config_for_environment()
    
    for attempt in range(max_retries):
        try:
            validate_config(config)
            await monitoring_integration.initialize(config)
            logger.info(f"Monitoring initialized successfully on attempt {attempt + 1}")
            return True
        except Exception as e:
            logger.warning(f"Monitoring initialization attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error("Failed to initialize monitoring after all retries")
                return False


def get_monitoring_middleware():
    """Get the monitoring middleware for manual addition to FastAPI app."""
    return MonitoringMiddleware


def get_monitoring_router():
    """Get the monitoring router for manual inclusion in FastAPI app."""
    return monitoring_router


# Example usage functions
async def example_startup_integration():
    """Example of how to integrate monitoring in application startup."""
    
    # Method 1: Using lifespan context manager
    app = FastAPI(lifespan=monitoring_lifespan)
    
    # Method 2: Using setup function
    app = FastAPI()
    setup_monitoring_app(app)
    
    # Method 3: Manual setup
    app = FastAPI()
    
    @app.on_event("startup")
    async def startup():
        config = get_config_for_environment()
        await initialize_monitoring_with_retry(config)
    
    @app.on_event("shutdown")
    async def shutdown():
        await monitoring_integration.shutdown()
    
    app.add_middleware(MonitoringMiddleware)
    app.include_router(monitoring_router)


# Configuration helpers
def print_config_documentation():
    """Print configuration documentation."""
    from .environment_config import ENV_VARS_DOCUMENTATION
    print(ENV_VARS_DOCUMENTATION)


def validate_environment_config():
    """Validate current environment configuration."""
    try:
        config = get_config_for_environment()
        validate_config(config)
        print("✅ Configuration is valid")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


if __name__ == "__main__":
    # CLI utility for configuration validation
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        validate_environment_config()
    elif len(sys.argv) > 1 and sys.argv[1] == "docs":
        print_config_documentation()
    else:
        print("Usage:")
        print("  python startup_integration.py validate  - Validate configuration")
        print("  python startup_integration.py docs      - Show configuration docs")