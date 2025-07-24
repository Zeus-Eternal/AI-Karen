"""
Enhanced FastAPI application factory for AI Karen engine.
"""

import os
from typing import Optional, Dict, Any

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.gzip import GZipMiddleware
except ImportError:
    from ai_karen_engine.fastapi_stub import FastAPI
    CORSMiddleware = object
    GZipMiddleware = object

from ai_karen_engine.core.services import ServiceContainer, get_container
from ai_karen_engine.core.errors import error_middleware
from ai_karen_engine.core.logging import logging_middleware, get_logger
from ai_karen_engine.core.gateway.middleware import setup_middleware
from ai_karen_engine.core.gateway.routing import setup_routing

logger = get_logger(__name__)


class KarenApp:
    """
    Enhanced FastAPI application wrapper with service integration.
    """
    
    def __init__(
        self,
        title: str = "AI Karen Engine",
        description: str = "AI Karen Engine API Gateway",
        version: str = "1.0.0",
        debug: bool = False,
        service_container: Optional[ServiceContainer] = None
    ):
        self.title = title
        self.description = description
        self.version = version
        self.debug = debug
        self.service_container = service_container or get_container()
        
        # Create FastAPI app
        self.app = FastAPI(
            title=title,
            description=description,
            version=version,
            debug=debug,
            docs_url="/docs" if debug else None,
            redoc_url="/redoc" if debug else None,
            openapi_url="/openapi.json" if debug else None,
            root_path=os.getenv("KAREN_API_ROOT", ""),
        )
        
        # Setup middleware and routing
        self._setup_app()
    
    def _setup_app(self) -> None:
        """Setup application middleware and routing."""
        # Setup middleware
        setup_middleware(self.app, debug=self.debug)
        
        # Setup routing
        setup_routing(self.app, self.service_container)
        
        # Setup startup and shutdown events
        self._setup_events()
    
    def _setup_events(self) -> None:
        """Setup application startup and shutdown events."""
        
        @self.app.on_event("startup")
        async def startup_event():
            """Application startup event."""
            logger.info("Starting AI Karen Engine")
            
            try:
                # Start all services
                await self.service_container.start_all_services()
                logger.info("All services started successfully")
                
            except Exception as e:
                logger.error(f"Failed to start services: {e}")
                raise
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            """Application shutdown event."""
            logger.info("Shutting down AI Karen Engine")
            
            try:
                # Stop all services
                await self.service_container.stop_all_services()
                logger.info("All services stopped successfully")
                
            except Exception as e:
                logger.error(f"Failed to stop services: {e}")
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance."""
        return self.app
    
    def add_service(self, name: str, service_class, config, singleton: bool = True) -> None:
        """
        Add a service to the container.
        
        Args:
            name: Service name
            service_class: Service class
            config: Service configuration
            singleton: Whether to create singleton instance
        """
        self.service_container.register_service(name, service_class, config, singleton)
    
    def get_service(self, name: str):
        """
        Get a service from the container.
        
        Args:
            name: Service name
            
        Returns:
            Service instance
        """
        return self.service_container.get_service(name)


def create_app(
    title: str = "AI Karen Engine",
    description: str = "AI Karen Engine API Gateway", 
    version: Optional[str] = None,
    debug: Optional[bool] = None,
    config: Optional[Dict[str, Any]] = None
) -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Args:
        title: Application title
        description: Application description
        version: Application version
        debug: Debug mode
        config: Additional configuration
        
    Returns:
        Configured FastAPI application
    """
    # Get configuration from environment if not provided
    if version is None:
        version = os.getenv("KAREN_VERSION", "1.0.0")
    
    if debug is None:
        debug = os.getenv("KAREN_DEBUG", "false").lower() == "true"
    
    # Create Karen app
    karen_app = KarenApp(
        title=title,
        description=description,
        version=version,
        debug=debug
    )
    
    # Apply additional configuration if provided
    if config:
        for key, value in config.items():
            setattr(karen_app, key, value)
    
    logger.info(f"Created AI Karen Engine app: {title} v{version}")
    
    return karen_app.get_app()
